# Decisions made

As many sets of convoy paradoxes can tell you, creating a Diplomacy tool is no joke! Due to this, some decisions have to be made. This document exists to catalogue these decisions and the reasons why they were made.

## Use Cases

The most important decision for a tool which is supposed to be used by multiple people. The intended use case for the tool is to connect it to a screen and let that replace the board for an in-person Diplomacy game. This allows for quicker adjudication than at the board, but avoids the problems with online submission. As such, the view is expected to be running in a sandbox mode.

## Modularity

One of the crucial decisions that came up was to decide to what level the tool needs to be modular. The initial prototype functioned, but suffered from the following problems:
* Control or state-focused code in the View module. When it came time to interface with an adjudicator, this translated to two separate sets of state being tracked, where the View was updating the adjudicator when adjudication was necessary.
* Dense and hard-to-parse adjudicator. While I understood each individual part of the adjudication, all of the interfacing functionality got in the way and made the overall class into a formidable wall of code.
* Hard-coded test cases. Since the test cases weren't available in a format other than text for human reading, the modularity of this was minimal.
* Overall low abstraction and high coupling - Units defined in the Adjudicator were the same units as used by the model. This meant that the adjudicator created a list of units without image data attached.

Thus, I decided that a refactor was necessary in order to modularise the entire tool better and improve on all of these with a few key points:
* Strong emphasis on interfacing.
    * For example, I began with the Adjudicator<->Test interface. The testing side of the interface demands a set of basic functions and wraps the adjudicator to handle all the specifics of the interface, while allowing the main testing module to focus on the test cases and how to display them.
* Using inheritance to make more parse-able and decoupled classes.
    * The Adjudicator side of the Adjudicator<->Test interface has a BaseAdjudicator, which does what it can to implement the required functions and their usage. This allows the main Adjudicator class to focus only on how it adjudicates a certain moveset.
* Stricter separation into Model-View-Controller components.
    * I created a diplomacy_utils file, which contains utilities and base classes for the building blocks of the model. This allows the View module to extend these classes and apply its own visual necessities without interrupting the functionality of the other modules, and without needing to redefine Model code on these descendants.

## Intentionally Failed Test Cases

DATC 3.1 has the following test cases which this tool intentionally fails:
