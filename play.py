#!/usr/bin/env python3
import os
import random
import sys
import time

from generator.gpt2.gpt2_generator import *
from story import grammars
from story.story_manager import *
from story.utils import *

from tgio import print, console_print, input, is_ready, get_num_options, _print as native_print

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def splash():
    print("0) New Game\n1) Load Game\n")
    choice = get_num_options(2)

    if choice == 1:
        return "load"
    else:
        return "new"


def random_story(story_data):
    # random setting
    settings = story_data["settings"].keys()
    n_settings = len(settings)
    rand_n = random.randint(0, n_settings - 1)
    for i, setting in enumerate(settings):
        if i == rand_n:
            setting_key = setting

    # temporarily only available in fantasy
    setting_key = "fantasy"

    # random character
    characters = story_data["settings"][setting_key]["characters"]
    n_characters = len(characters)
    rand_n = random.randint(0, n_characters - 1)
    for i, character in enumerate(characters):
        if i == rand_n:
            character_key = character

    # random name
    name = grammars.direct(setting_key, "fantasy_name")

    return setting_key, character_key, name, None, None


def select_game():
    with open(YAML_FILE, "r") as stream:
        data = yaml.safe_load(stream)

    # Random story?
    print("Random story?")
    console_print("0) yes")
    console_print("1) no")
    choice = get_num_options(2)

    if choice == 0:
        return random_story(data)

    # User-selected story...
    print("\n\nPick a setting.")
    settings = data["settings"].keys()
    for i, setting in enumerate(settings):
        print_str = str(i) + ") " + setting
        if setting == "fantasy":
            print_str += " (recommended)"

        console_print(print_str)
    console_print(str(len(settings)) + ") custom")
    choice = get_num_options(len(settings) + 1)

    if choice == len(settings):
        return "custom", None, None, None, None

    setting_key = list(settings)[choice]

    print("\nPick a character")
    characters = data["settings"][setting_key]["characters"]
    for i, character in enumerate(characters):
        console_print(str(i) + ") " + character)
    character_key = list(characters)[get_num_options(len(characters))]

    name = input("\nWhat is your name? ")
    setting_description = data["settings"][setting_key]["description"]
    character = data["settings"][setting_key]["characters"][character_key]

    return setting_key, character_key, name, character, setting_description


def get_custom_prompt():
    context = ""
    console_print(
        "\nEnter a prompt that describes who you are and the first couple sentences of where you start "
        "out ex:\n 'You are a knight in the kingdom of Larion. You are hunting the evil dragon who has been "
        + "terrorizing the kingdom. You enter the forest searching for the dragon and see' "
    )
    prompt = input("Starting Prompt: ")
    return context, prompt


def get_curated_exposition(
    setting_key, character_key, name, character, setting_description
):
    name_token = "<NAME>"
    if (
        character_key == "noble"
        or character_key == "knight"
        or character_key == "wizard"
    ):
        context = grammars.generate(setting_key, character_key, "context") + "\n\n"
        context = context.replace(name_token, name)
        prompt = grammars.generate(setting_key, character_key, "prompt")
        prompt = prompt.replace(name_token, name)
    else:
        context = (
            "You are "
            + name
            + ", a "
            + character_key
            + " "
            + setting_description
            + "You have a "
            + character["item1"]
            + " and a "
            + character["item2"]
            + ". "
        )
        prompt_num = np.random.randint(0, len(character["prompts"]))
        prompt = character["prompts"][prompt_num]

    return context, prompt


def instructions():
    text = "\nAI Dungeon 2 Instructions:"
    text += '\n Enter actions starting with a verb ex. "go to the tavern" or "attack the orc."'
    text += '\n To speak enter \'say "(thing you want to say)"\' or just "(thing you want to say)" '
    text += "\n\nThe following commands can be entered for any action: "
    text += '\n  "/revert"   Reverts the last action allowing you to pick a different action.'
    text += '\n  "/quit"     Quits the game and saves'
    text += '\n  "/restart"  Starts a new game and saves your current one'
    text += '\n  "/save"     Makes a new save of your game and gives you the save ID'
    text += '\n  "/load"     Asks for a save ID and loads the game if the ID is valid'
    text += '\n  "/print"    Prints a transcript of your adventure (without extra newline formatting)'
    text += '\n  "/help"     Prints these instructions again'
    text += '\n  "/censor off/on" to turn censoring off or on.'
    return text


def play_aidungeon_2():

    console_print(
        "AI Dungeon 2 will save and use your actions and game to continually improve AI Dungeon."
        + " If you would like to disable this enter '/nosaving' as an action. This will also turn off the "
        + "ability to save games."
    )

    upload_story = True

    print("\nInitializing AI Dungeon! (This might take a few minutes)\n")
    generator = GPT2Generator()
    story_manager = UnconstrainedStoryManager(generator)
    print("\n")

    # broken formatting in tg
    #with open("opening.txt", "r", encoding="utf-8") as file:
    #    starter = file.read()
    #print(starter)

    while True:
        if story_manager.story != None:
            story_manager.story = None

        while story_manager.story is None:
            print("\n\n")
            splash_choice = splash()

            if splash_choice == "new":
                print("\n\n")
                (
                    setting_key,
                    character_key,
                    name,
                    character,
                    setting_description,
                ) = select_game()

                if setting_key == "custom":
                    context, prompt = get_custom_prompt()

                else:
                    context, prompt = get_curated_exposition(
                        setting_key, character_key, name, character, setting_description
                    )

                console_print(instructions())
                print("\nGenerating story...")

                result = story_manager.start_new_story(
                    prompt, context=context, upload_story=upload_story
                )
                print("\n")
                console_print(result)

            else:
                load_ID = input("What is the ID of the saved game? ")
                result = story_manager.load_new_story(
                    load_ID, upload_story=upload_story
                )
                print("\nLoading Game...\n")
                console_print(result)

        while True:
            sys.stdin.flush()
            action = input("> ").strip()
            if len(action) > 0 and action[0] == "/":
                split = action[1:].split(" ")  # removes preceding slash
                command = split[0].lower()
                args = split[1:]
                if command == "restart":
                    while True:
                        try:
                            rating = input("Please rate the story quality from 1-10: ")
                            rating_float = max(min(float(rating), 10), 1)
                        except ValueError:
                            print("Please return a valid number.")
                        else:
                            story_manager.story.rating = rating_float
                            break
                    break

                elif command == "quit":
                    while True:
                        try:
                            rating = input("Please rate the story quality from 1-10: ")
                            rating_float = max(min(float(rating), 10), 1)
                        except ValueError:
                            print("Please return a valid number.")
                        else:
                            story_manager.story.rating = rating_float
                            break
                    exit()

                elif command == "nosaving":
                    upload_story = False
                    story_manager.story.upload_story = False
                    console_print("Saving turned off.")

                elif command == "help":
                    console_print(instructions())

                elif command == "censor":
                    if len(args) == 0:
                        if generator.censor:
                            console_print("Censor is enabled.")
                        else:
                            console_print("Censor is disabled.")
                    elif args[0] == "off":
                        if not generator.censor:
                            console_print("Censor is already disabled.")
                        else:
                            generator.censor = False
                            console_print("Censor is now disabled.")

                    elif args[0] == "on":
                        if generator.censor:
                            console_print("Censor is already enabled.")
                        else:
                            generator.censor = True
                            console_print("Censor is now enabled.")

                    else:
                        console_print(f"Invalid argument: {args[0]}")

                elif command == "save":
                    if upload_story:
                        id = story_manager.story.save_to_storage()
                        console_print("Game saved.")
                        console_print(
                            f"To load the game, type 'load' and enter the following ID: {id}"
                        )
                    else:
                        console_print("Saving has been turned off. Cannot save.")

                elif command == "load":
                    if len(args) == 0:
                        load_ID = input("What is the ID of the saved game?")
                    else:
                        load_ID = args[0]
                    result = story_manager.story.load_from_storage(load_ID)
                    console_print("\nLoading Game...\n")
                    console_print(result)

                elif command == "print":
                    print("\nPRINTING\n")
                    print(str(story_manager.story))

                elif command == "revert":
                    if len(story_manager.story.actions) == 0:
                        console_print("You can't go back any farther. ")
                        continue

                    story_manager.story.actions = story_manager.story.actions[:-1]
                    story_manager.story.results = story_manager.story.results[:-1]
                    console_print("Last action reverted. ")
                    if len(story_manager.story.results) > 0:
                        console_print(story_manager.story.results[-1])
                    else:
                        console_print(story_manager.story.story_start)
                    continue

                else:
                    console_print(f"Unknown command: {command}")

            else:
                if action == "":
                    action = ""
                    result = story_manager.act(action)
                    console_print(result)

                elif action[0] == '"':
                    action = "You say " + action

                else:
                    action = action.strip()
                    action = action[0].lower() + action[1:]

                    if "You" not in action[:6] and "I" not in action[:6]:
                        action = "You " + action

                    if action[-1] not in [".", "?", "!"]:
                        action = action + "."

                    action = first_to_second_person(action)

                    action = "\n> " + action + "\n"

                result = "\n" + story_manager.act(action)
                if len(story_manager.story.results) >= 2:
                    similarity = get_similarity(
                        story_manager.story.results[-1], story_manager.story.results[-2]
                    )
                    if similarity > 0.9:
                        story_manager.story.actions = story_manager.story.actions[:-1]
                        story_manager.story.results = story_manager.story.results[:-1]
                        console_print(
                            "Woops that action caused the model to start looping. Try a different action to prevent that."
                        )
                        continue

                if player_won(result):
                    console_print(result + "\n CONGRATS YOU WIN")
                    break
                elif player_died(result):
                    console_print(result)
                    console_print("YOU DIED. GAME OVER")
                    console_print("\nOptions:")
                    console_print("0) Start a new game")
                    console_print(
                        "1) \"I'm not dead yet!\" (If you didn't actually die) "
                    )
                    console_print("Which do you choose? ")
                    choice = get_num_options(2)
                    if choice == 0:
                        break
                    else:
                        console_print("Sorry about that...where were we?")
                        console_print(result)

                else:
                    console_print(result)


if __name__ == "__main__":
    native_print('Now you should initiate dialogue with your bot!')
    while not is_ready():
        time.sleep(3)
    play_aidungeon_2()
