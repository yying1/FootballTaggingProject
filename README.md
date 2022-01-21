# FootballTaggingProject

---
#### Quicklinks:

1. Where can I get the software? [Link](https://github.com/yying1/FootballTaggingProject/blob/main/README.md#set-up-requirements)
2. How can I use this? [Link](https://github.com/yying1/FootballTaggingProject/wiki/Workflow-and-Guideline)
---

### Background: 
In 1 sentence: This software can be used to tag events in football (soccer) match video and export data for analytics purposes. 

I was watching a soccer game replay back in Fall 2021 and really wanted to review the game from a different perspective. This new perspective should be data-driven and present game events across space (position on the field) and time (time mark of the game). I interned at [Hudl](https://www.hudl.com/) back in 2017 and familiarized myself with the concept of video-based analytic tools to help sports team stakeholders understand the game beyond just the video. However, most professional software licenses cost around 2000 - 5000 USD per year and are often bundled with other services and tools as packages. Since I just took a python programming course, I decided to use my winter break to develop this Football (Soccer) Tagging Software.

### Last Updated: 
2022-01-21

### Documentation
1. Product Road Map: [Google Doc](https://docs.google.com/document/d/1rgXGsRRUtFURbPx9At1lktV8gEviWlC9QfzNNFc0S9k/edit?usp=sharing)
2. Product Requirement Document: [Google Doc](https://docs.google.com/document/d/1J__imhIn6qVkLKvyYzS5VGSkRql9BwSibdP-wLo9f0w/edit?usp=sharing)
3. Product Wiki: [Google Doc](https://docs.google.com/document/d/13VXZbe1Mxj5Hmty57-uIgNOK_1UJK89dUC0JE0NRANw/edit?usp=sharing)

### Overview of the Product 
Leveraging the insights from this great web-based tool by FC Python, this product is a Python-based GUI application to tag match events given a football match video, which can be exported into a tabular format document for further analysis. The primary user identified for this product is sports analysts, who often collect game data for the coaches and data scientists. Therefore, sports analysts would want to collect both spatial and temporal data on events as multi-dimensional game stats.
Here are the child user stories from a sports analyst:
1. I want to know where the game event is happening on the pitch so that I can build an analysis around spatial factors.
2. I want to know when the game event takes place so that I can relate other events before and after to build a story.
3. I want to know who creates/belongs to the game event so that I can aggregate event data by players.
4. I want to link the data with video clips of the game so that I can review both pieces of the content together.
5. I want to collect and store the data in a format to store in the database for future analysis and data mining.

### Set-up Requirements
This application was built and tested in the following environment:
1. Windows 10 Pro Laptop with Intel Processor
2. Python 3.10
3. VLC Media Player [(download)](https://www.videolan.org/vlc/)
	
I also used the following python packages that are required to run this application:
1. PIL, for adding pictures to the UI
2. Tkinter, main UI framework
3. Vlc, video player function embedded in the UI
4. Pandas, for storing and exporting the event tag data

You will need the following files to run this application:
1. \src\FootballTaggingApp.py, the main script for this application
2. \src\Field.jpg, a self-made grid of standard soccer pitch for location tracking
	
***How to run this application?***
1. Copy FootballTaggingApp.py and Field.jpg to the same local directory
2. Double click on the .py file or run with your choice of Python editor

### More:

For more information about this project and the software, plese visit the [Wiki](https://github.com/yying1/FootballTaggingProject/wiki) page!
