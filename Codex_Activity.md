**Sohail Mohammed Khan and Dooley Kim**

Dataset: [Minneapolis Scooter and eBike Trips 2025](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore).

# Macalester DS 456 - Projects in Data Science - Codex Activity

*Originally created by Shilad Sen (with help from Codex), 2025/11/25. Updated by Bret Jackson 2026/11/08*

In this activity you will:

- Use Codex as a collaborator on a real spatial dataset.
- Practice being *critical* of Codex’s suggestions (not just accepting them).
- Progress from exploration to a reviewed analysis plan, implement it with Codex, and verify one important result.

# 0. Get the project

- Fork the [Codex Activity](https://github.com/bretjackson/ds-456-codex-activity) on GitHub.
- Clone **your fork** (not the original) to your computer.

# 1. Choose your tools and set up Codex

You may work in **Python (VS Code)** or **R (VS Code or RStudio)**.

## 1.1 Highly Recommended: VS Code + Codex (Python or R)

- Install [VS Code](https://code.visualstudio.com/).
- Install the [Codex VS Code extension](https://developers.openai.com/codex/ide/).
- If you are using R, also install the [VS Code R extension](https://marketplace.visualstudio.com/items?itemName=reditorsupport.r).
- Open your cloned repo folder in VS Code.
- In the Codex sidebar:
  - Click “Use API Key” and use the key Shilad gave you.\
    **DO NOT PUT THIS KEY ANYWHERE IN YOUR GITHUB REPO.**
  - Open Codex settings → “Open `config.toml`” and set it to:
    ```toml
    model = "gpt-6.1-sol"
    model_reasoning_effort = "medium"
    web_search = "live"

    [sandbox_workspace_write]
    network_access = true
    ```
  - Restart VS Code after editing `config.toml`.

## 1.2 Optional: RStudio + Codex in a separate terminal

If you strongly prefer RStudio:

- Use **RStudio** for your R scripts / Rmd files.
- Using a terminal, install the Codex CLI: `npm i -g @openai/codex`
- In a terminal, run `codex` once so it creates a config file at `~/.codex/config.toml`.
- Open `~/.codex/config.toml` in any text editor you like (VS Code, TextEdit, Notepad, `nano`, etc.) and paste the same settings shown in 1.1.
- In a separate terminal window (**from the repo root**), run Codex and use it to:
  - Draft and refactor R code.
  - Ask questions about errors.
- You are still responsible for keeping all code and writeups in this repo so they can be graded.

# 2. Create your assignment skeleton

You will **not** edit this `README.md` directly. Instead:

- Copy `README.md` to `Codex_Activity.md`.
- Add your name(s) at the top of `Codex_Activity.md`.
- For every prompt marked **Task:** below, you will write your answers in `Codex_Activity.md`.
- Your actual analysis code should live in code files, for example:
  - R: `analysis/codex_activity.qmd` or `analysis/codex_activity.R`
  - Python: `analysis/codex_activity.ipynb` or `analysis/codex_activity.py`

You may reference your code files from `Codex_Activity.md` (e.g., “see Figure 1 in `analysis/codex_activity.Rmd`”).

Keep using the same Codex conversation as you move from exploration to mapping and analysis, including when you return for the second class session. If you start a new conversation, provide your research question (if chosen), relevant file paths, and a short summary of what you have discovered.

# 3. Early dataset interactions

- Pick a spatial dataset from [Open Data Minneapolis](https://opendata.minneapolismn.gov).\
  One fun option (used in the instructor example) is\
  [Motorized Foot & eBike Trips in 2025](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore).
- Give Codex the URL for the dataset and ask it to help you get started understanding the data.\
  Keep your request intentionally vague (e.g., “Help me explore this dataset”).

**Task 3.1 (in `Codex_Activity.md`):**\
In 2–3 short bullets, describe what you notice about this early interaction. Consider:

- What did Codex assume or gloss over?
- Did it make any mistakes or questionable choices?
- How clear or explainable was the code it produced?

Retain useful code and observations from this interaction so you can build on them in the next sections.

### Task 3.1 response

- Codex started with Python and the city's API without asking what we wanted to focus on. It did check the units and catch the conflicting 2024/2025 descriptions.
- It clearly labeled the first 1,000 rows as an ordered preview, not a random sample.
- The code had comments but was longer than necessary. Changes to the saved writeup also caused confusion because our editor showed an older version.

# 4. More directed exploration

- If you are partner coding, *switch partners*.
- Download the dataset you would like to analyze and move it under `data/`.
- Ask Codex to help you analyze the **basic information** about the dataset:
  - basic summaries (rows, columns, variable types),
  - simple visualizations,
  - any surprising patterns.
- Then ask Codex for specific improvements (e.g., “Use `dplyr` instead of base R”, “Add labels and titles”, “Handle missing values more carefully”).
- Save useful exploration code in your analysis file and keep notes about relevant variables and assumptions. You will reuse this work for mapping and your research question.

**Task 4.1 (in `Codex_Activity.md`):**
Respond in 2–3 short bullets, considering:

- What did Codex do well?
- What would you have done differently if you wrote the code yourself?
- Looking at the code Codex wrote, what could be improved (style, clarity, correctness, efficiency)?

### Task 4.1 response

- Codex summarized all **1,024,014 trips and 11 columns** and made labeled charts. The mean duration was **12.51 minutes**, compared with a median of **7.87 minutes**.
- We'd start with the full CSV and a shorter pandas script next time. The API requests and custom plotting code added complexity.
- Missing locations needed careful handling: **17,551 trail starts** and **17,823 trail ends** lack IDs. These trips can still be included in duration and distance summaries.

Duration and distance are numeric measurements; vehicle and centerline types are categories; start/end times are datetimes. The remaining fields are identifiers. The full dataset is **76.05% scooters** and **23.95% bicycles**, which the source describes as e-bikes.

| Measurement | Mean | Median |
|---|---:|---:|
| Duration (minutes) | 12.51 | 7.87 |
| Distance (kilometers) | 2.31 | 1.56 |

See the [exploration charts and variable summaries](Analysis/outputs/exploration.md) and [exploration code](Analysis/Codex_activity.py).

# 5. Mapping the data

- If you are partner coding, *switch partners*.
- Discuss with your partner how you could geocode / map the data.
- Once you have an idea for how to do it, ask Codex to help you map your data. Pay attention to what happens at first:
  - Does it correctly identify what is needed to make a map?
  - Does it confuse attributes (like IDs) with coordinates?

- For the scooter/e‑bike example, the goal is to join trips to a street or trail network such as the\
  [PW Street Centerline dataset](https://opendata.minneapolismn.gov/datasets/pw-street-centerline/about) and then map trip counts by segment.
- Identify a calculation, join, coordinate interpretation, or mapped value you could verify later. In Section 7.3, you will be asked to do some verification.

**Task 5.1 (in `Codex_Activity.md`):**
Respond in 2–3 short bullets, considering:

- Describe what was easier and harder about doing this with Codex.
- Where did Codex help, and where did it get in the way?
- What would you do differently next time you had to map a new dataset with AI assistance?

### Task 5.1 response

- Codex found the street network and correctly treated centerline IDs as join keys, not coordinates.
- Checking the join was harder than drawing the map. We excluded unmatched IDs and IDs that appeared more than once in the network to avoid assigning trips to uncertain locations.
- Next time, we'd check key uniqueness and match coverage first. Here, **895,767 starts (87.48%)** matched one street feature.

The map excludes **17,551 nonstreet starts**, **95,001 starts with unmatched street IDs**, and **15,695 starts with ambiguous IDs**. These plus the mapped starts account for all trips. It shows start locations, not routes.

![Trip starts by street segment](Analysis/outputs/trip_start_counts_map.svg)

Code: [spatial_analysis.py](Analysis/spatial_analysis.py). Details: [join audit](Analysis/outputs/spatial_audit.json).

# 6. Identifying a research question with Codex

- If you are partner coding, *switch partners*.
- You will now work with Codex to identify and refine a research question (RQ) about your dataset.
- Choose a question you can answer with the downloaded data and a small extension of your existing exploration or mapping code. A descriptive question is sufficient; aim for an analysis you can implement in about 20 minutes.

## 6.1 Brainstorm candidate questions

- Seed the brainstorming session with some themes or ideas of research questions that interest you.
- Ask Codex to propose several possible research questions.
- Collaborate with Codex to prioritize the questions along the decision dimensions you think are most appropriate.

**Task 6.1 (in `Codex_Activity.md`):**

- List at least two candidate research questions that Codex suggested.
- For each, briefly note what seems interesting and what might be problematic (data, scope, ethics, feasibility).

### Task 6.1 response

- **How do duration and distance differ between scooters and e-bikes?** Easy to answer with existing fields, but long trips could pull up averages. We'd need medians and the recorded duration because timestamps are rounded.
- **How do scooter and e-bike shares vary across start segments?** Builds on the map and shows local differences. Missing locations and segments with few starts could affect the comparison.

## 6.2 Refine and choose your question

- Pick one question (it may be a slight modification of a Codex suggestion).
- Ask Codex to critique and refine that question. For example:
  - “Here is my tentative research question: […]. Critique its clarity and feasibility. Propose 1–2 improved versions.”
- Decide on a **final RQ** you will try to answer. This choice is yours, not Codex’s.

**Task 6.2 (in `Codex_Activity.md`):**

- Write down your final research question in one clear sentence.
- In 2–3 sentences, explain why you chose it (and why you rejected other candidates).

### Task 6.2 response

**How do scooter and e-bike shares of trip starts vary across Minneapolis street segments in the 2025 release, using segments that match one street feature and have at least 100 starts?**

We chose this because it builds on our map and looks at differences between places. The duration question was also feasible, but it made less use of the spatial data.

# 7. Answering your question: plan, implement, and verify

Build on your exploration and map to answer **one research question**. Review a plan with Codex, implement it, and verify one important result or transformation.

## 7.1 Design and review a plan

**Plan mode** lets Codex inspect context, ask clarifying questions, and propose an approach before implementation. It can investigate existing files; it should not implement your analysis while planning. See the [OpenAI guidance on Plan mode](https://learn.chatgpt.com/docs/learn/best-practices).

1. Wait until Codex finishes its current response.
2. In the **Codex chat input inside VS Code**, enter `/plan`, select the command, and press Enter. Check that Plan mode is active. If using Codex CLI alongside RStudio, enter the command in the Codex conversation in your terminal.
3. Submit your planning request and answer any clarifying questions.
4. Review and revise the proposed plan before leaving Plan mode.

Review the plan yourself:

- Does it answer your chosen question using available data?
- Are the units, filters, grouping, and treatment of missing values appropriate?
- Does it reuse relevant exploration or mapping work?
- Is the proposed verification feasible and capable of detecting a meaningful error?

Ask Codex to clarify or revise anything you cannot justify. If you do not understand the type of analysis or choices it is suggesting, stop! Discuss them with your partner and clarify with Codex.

**Task 7.1 (in `Codex_Activity.md`):**

- Record your final plan in 3–5 bullets.
- Explain one decision you made while reviewing it. A justified decision to retain a proposed approach counts; you do not need to change the plan just to make a change. However, don't just blindly accept what it suggests. Stop and discuss each decision with your partner!

### Task 7.1 response

- Use the full CSV, check TripID uniqueness, and count scooter and bicycle street starts by start ID. Join only IDs that match one street feature, recording exclusions.
- Keep segments with **at least 100 starts**. Calculate scooter share as scooter starts divided by scooter plus bicycle starts; bicycle share is the remainder.
- Compare minimums of 50, 100, and 200 starts to see how much the overall scooter share changes. Keep 100 for the main results.
- Map counts and shares, then summarize the share range and how many segments have a majority of each vehicle type.
- Check four segments against the city's services, including one with a bicycle majority. Also check that an ambiguous street ID is excluded rather than counted twice.

**Decision and reason:** We kept the 100-start minimum after comparing 50, 100, and 200. The overall scooter share changes only from 76.82% to 78.02%, so 100 is a reasonable middle ground: it reduces the influence of small counts while retaining 1,775 segments, compared with 1,033 at a minimum of 200. It does not guarantee that every segment's percentage is reliable.

| Minimum starts | Segments | Trip starts | Overall scooter share |
|---|---:|---:|---:|
| 50 | 2,641 | 822,091 | 76.82% |
| 100 | 1,775 | 760,736 | 77.27% |
| 200 | 1,033 | 655,339 | 78.02% |

Full values: [threshold comparison](Analysis/outputs/threshold_comparison.csv).

**Review timing:** We reviewed this plan in Plan mode **after the initial implementation**. We agreed to retain the main method, add the 50/100/200 comparison, and expand verification to include a bicycle-heavy segment and an ambiguous ID that should be excluded. Those additions were implemented after the review.

## 7.2 Implement and inspect

Use the `/plan` toggle to leave Plan mode and confirm it is off **before** requesting implementation, or Press the "Implement this plan" option if it appears.

- You can request the whole small plan or start with a meaningful first step and continue after inspecting it.
- Keep the work in the R or Python analysis file.
- Inspect the changed code and outputs. Does the analysis answer your question? Are the results interpretable and relevant?
- Ask targeted follow-up questions and revise as needed.

**Task 7.2 (in `Codex_Activity.md`):**

- Briefly state your result and link to the supporting figure, table, or code.
- Describe one implementation choice or issue you examined and what you decided about it.

### Task 7.2 response

The comparison covers **1,775 segments and 760,736 starts**. Scooter shares range from **7.91% to 98.61%**. Scooters have a majority on **1,686 segments**, bicycles on **86**, and **3** are tied. Overall, **77.27%** of these starts are scooters.

One issue was repeated GBSIDs: ID 11022 appeared on two pieces of 21ST AVE S. The revised code excludes all **251 repeated network IDs**, removing **15,695 starts** rather than duplicating counts or guessing a location.

![Scooter share on segments with at least 100 starts](Analysis/outputs/scooter_share_map.svg)

See the [results](Analysis/outputs/spatial_analysis.md) and [segment table](Analysis/outputs/segment_vehicle_shares.csv).

## 7.3 Verify one important result and reflect

Perform **one documented check** of a consequential claim, calculation, or transformation from your exploration, mapping, or final analysis.

Choose a check suited to your dataset. Here are some possibilities you could consider:

| Check | Evidence you could provide |
|---|---|
| Recalculate a summary | Manually compute a count, mean, or percentage for a small identified subset and compare it with the code's result for that subset. |
| Check a join used in mapping | Inspect several known matches against the source records and account for unmatched or duplicated records. |
| Check mapped locations | Compare several identifiable features with an authoritative reference and record specific matches or discrepancies. |
| Check a derived variable | Use documented units and a few source records to calculate expected values independently and compare them with the derived values. |

Successful execution, a plausible-looking map, or Codex saying “this is correct” does not satisfy this requirement. Codex may help write checking code, but **you must explain the basis of the check and inspect its evidence**. Establish an expected result or reference independently of the output you are checking.

**Task 7.3 (in `Codex_Activity.md`):**

Record:

- **What I checked and why it matters.**
- **How I checked it**, including the independently established expectation or reference.
- **What I observed**, with actual values, identified records, or another concrete comparison.
- **What I changed or concluded**, including the result of rechecking any correction.


### Task 7.3 response

- **What and why:** Check the counts, scooter share, and street join for GBSID **16907**, since a wrong join or denominator would affect the map.
- **Reference:** A separate city trip-service query returned **1,480 scooter starts and 260 bicycle starts**. The street service identifies this as **6TH AVE N, from 3RD ST N to WASHINGTON AVE N**. These references came from the services, not our local output.
- **Comparison:** The expected share is **1480 / (1480 + 260) × 100 = 85.0575%**. The analysis gives the same counts, share, and street names.
- **Conclusion:** All four mapped segments and the ambiguous-ID exclusion pass. No further correction to the main results was needed. These checks support the selected cases, not every segment or the accuracy of the original trip data.

**Added after review:** GBSID **14327** was chosen because bicycles have a majority. The city service confirms **11 scooter and 128 bicycle starts**, giving **11 / 139 × 100 = 7.9137%** scooters; the counts, share, and street names match the output. GBSID **11022** was chosen because it caused the repeated-key issue. The street service returns **two features**, and the trip service confirms **96 scooter + 24 bicycle = 120 starts**. It is absent from the mapped table and appears once in the exclusions with those counts and the reason `ambiguous_network_id`. The original checks for 16907, 17120, and 19543 also still pass.

The [verification report](Analysis/outputs/verification.md), [source queries and responses](Analysis/outputs/verification_reference.json), and [checking code](Analysis/verify_spatial.py) contain the evidence.

# 8. What to hand in

By the end of the activity, your repo should include at least:

- `Codex_Activity.md` with answers to all **Task** prompts (3.1, 4.1, 5.1, 6.1, 6.2, 7.1, 7.2, 7.3), including your reviewed plan, research-question result, and verification evidence.
- At least one analysis file:
  - R: `analysis/codex_activity.qmd` or `analysis/codex_activity.R`
  - Python: `analysis/codex_activity.ipynb` or `analysis/codex_activity.py`
- At least one map saved in the repo and linked from your writeup, or embedded in your analysis/writeup.
- Any additional scripts or notebooks you used, committed in a reasonable state.

Before you’re done:

- Use Codex to help you **commit and push** your work to your forked repo.
- Make sure that your API key is **not** anywhere in the repo.
- Share the URL for the repo (including the markdown and script) on the Moodle activity.

## Interpretation and limits

- Duration is in seconds and distance in meters; the tables convert them to minutes and kilometers. Rounded timestamps should not be used to calculate trip duration.
- The title says 2025 but the description mentions 2024. UTC start times actually span April 8, 2025 through January 1, 2026; local dates can differ.
- The current street network may differ from the 2025 network. Missing and excluded locations could change the vehicle mix we see.
- These are recorded start shares, not routes or rider preferences. Availability, pricing, and other possible explanations weren't tested.


## Files

See [data/README.md](data/README.md) for downloads and rerun commands. Code, maps, and verification are saved in [our fork](https://github.com/my-name-arch/ds-456-codex-activity).

