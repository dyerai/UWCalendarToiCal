# UW Calendar to ICal

UW Calendar to ICal is a simple python program that does exactly what it sounds like it would do.

## Description

This program takes in a UW-Madison course schedule and converts it to a .ics file with accurate location, room information, and of time/date information.

## Usage

### Dependencies
Once you clone this repo, install the required dependencies using `pip install -r requirements.txt`

### Executing program
 You can obtain the course schedule by following these steps:
  1. Go to MyUW and select the Course Schedule App
  2. In the Course Schedule App, press the print button
  3. In the print dialog, select "Save as PDF" as the destination

Once you've done this, simply run the script using `python3 uwtoical.py <path to schedule PDF>`
