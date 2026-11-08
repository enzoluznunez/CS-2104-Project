# Week 10 Final Project: Seeking Pips

Software Engineering | Submission and Final Report

**Project title:** Seeking Pips
**Student name:** Enzo Nunez  **PID:** enzonunez
**Course / section:** 83521

The submitted PDF of this report is [`Week_10_Final_Report.pdf`](Week_10_Final_Report.pdf).

## Submission links

- **Discovery deployment:** [Paste the working Discovery URL]
- **Private repository:** <https://github.com/enzoluznunez/CS-2104-Project>
- **Final demonstration:** Video attached in Canvas submission

## Honor code statement

As a Hokie, I will conduct myself with honor and integrity at all times. I will
not lie, cheat, or steal, nor will I accept the actions of those who do.

## LLM-use statement

I used Claude Code by Anthropic for code generation and debugging.

---

## Final report | Week 9 time comparison

### Planned time versus actual time

The Week 8 plan column keeps the original task details from the Week 8
proposal, unchanged.

| Task / milestone | Week 8 plan | Actual time and work |
| --- | --- | --- |
| Design the project structure and plan | **Planned hours:** 1<br><br>**Original details:** *The first step will be to create a local repository on GitHub with, then write the README, and install any necessary packages or libraries. I'll then use a Python script to get a hold of lots and lots of pip data from a whole bunch of different things like indices, stocks, futures, you name it, all of which I can get from Yahoo Finance. Once I have all the data, I can store it in Flask.* | **Actual hours:** 0.5<br><br>**Work completed:** Mapped out architecture, created repository and added GTAs.<br><br>**Changes from plan:** Shorter since I was familiar with GitHub and system design. |
| Code the basic functionality | **Planned hours:** 1<br><br>**Original details:** *I'll use one of the LLMs on ARC to go ahead and build out a website using HTML for the organization, CSS for style, and node.js for functionality. Once that's all in place, I can begin work on the features, like boxes to enter dates and select assets. The trick here will be to pace myself, and focus on gradual building.* | **Actual hours:** 0.5<br><br>**Work completed:** Set up Claude Code in my local folder and input project overview.<br><br>**Changes from plan:** Didn't take as long as I thought it would, used to Claude Code. |
| Test and debug the initial version | **Planned hours:** 1<br><br>**Original details:** *The trick with testing, whether its unit, integration, or even regression is to go slow, writing tests for a small feature, building that feature, running tests and making corrections until they pass, then rinsing and repeating for each part of the website. Again, ARC will be invaluable as a model like KIMI K3 is excellent for testing and general debugging.* | **Actual hours:** 1<br><br>**Work completed:** Tested basic functionality by walking through each subfolder.<br><br>**Changes from plan:** Unit was super fast, integration and regression took longer to set up. |
| Refine and prepare the submission | **Planned hours:** 1<br><br>**Original details:** *For this first submission, I would like the website running locally, with data living on Flask, and the website structure and basic features implemented. Some of these features include: a page to place bets, a page to track performance, and if I have the time, a page to compare how your doing to your friends, on an interactive leaderboard. These 3 pages will serve as the foundation for later work.* | **Actual hours:** 1<br><br>**Work completed:** Checking Canvas page and assignment template.<br><br>**Changes from plan:** Took about as long as expected since I double check. |

**Week 9 totals:** Planned: 4  Actual: 3

### Explain the comparison

The setup took a lot less longer than I expected because of, in my opinion, my
experience with using tools like GitHub and LLMs.

---

## Final report | Week 10 time comparison

### Planned time versus actual time

| Task / milestone | Week 8 plan | Actual time and work |
| --- | --- | --- |
| Design and code an additional feature | **Planned hours:** 1<br><br>**Original details:** *One feature that I think would be cool is a feature that gives users a quick and easy benchmark, something to compare their gambling to. It would take the amount of time the user was in the bet, find an event or investment the user could have made, using the same amount of money they just bet, and compare whether they would have made or lost compared to the bet.* | **Actual hours:** 1<br><br>**Work completed:** Debated between different benchmarks, landing on investments.<br><br>**Changes from plan:** Fleshed out feature from original plan. |
| Test and debug the final version locally | **Planned hours:** 1<br><br>**Original details:** *I would like to test each page while the site is still local, that includes the betting page, the performance page, and the leaderboard page, using KIMI K3 to write unit testing for each one, and regression testing for once I move away from local deployment and start hosting through Discovery.* | **Actual hours:** 0.25<br><br>**Work completed:** Used Claude Code for refining test cases.<br><br>**Changes from plan:** Switched from KIMI K3 to Claude Code. |
| Deploy, test, and debug | **Planned hours:** 1<br><br>**Original details:** *This will be where I lean on models form Google and OpenAI for deep, thorough testing and debugging once I am running on Discovery, including all those regressions tests from earlier. Edge cases can cause a lot of user friction and catching them quick makes all the difference when it comes to user experience.* | **Actual hours:** 2<br><br>**Work completed:** Deployed on Discover.<br><br>**Changes from plan:** Took a lot longer than expected, Discovery took longer to figure out. |
| Refine and prepare the final submission | **Planned hours:** 2<br><br>**Original details:** *This is where I get to really show my creativity, including video and report styling, giving them both my focus and attention as I wrap up the project. The website might be flawless but if I botch the landing then that won't do me any good, checking everything from the repository's hygiene to report's grammar will decide whether my final submission goes smoothly.* | **Actual hours:** 0.5<br><br>**Work completed:** Reviewed Canvas page and demo videos for local and hosted pages.<br><br>**Changes from plan:** Not that much. |

**Week 10 totals:** Planned: 5  Actual: 3.75

### Explain the comparison

Honestly the part that might not have taken the longest but was the most
confusing was deploying on Discovery. Even though I've used it before, I was
surprised at how long it took me to deploy.

---

## Final report | Consultation and use of LLMs

### Consultation description

I did not receive any consultation during this assignment.

### Use of LLMs

I used Claude Code by Anthropic in my local repository, including with /code
and /tests for example with writing HTML for structure and CSS for trying out
lots of website styles.

AI has a tendency to create pretty generic looking websites so I tried
prompting for a more unique style that I liked, changing between several color
themes and bet page layouts before landing on the final one.
