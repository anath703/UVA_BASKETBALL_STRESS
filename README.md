# Summary 
The main goal of this project was to prove our hypothesis that increased stress leads to poorer performance in college basketball players. We first created a Structural Equation Model (SEM) using survey and tracking data to capture the relationship between three latent variables: physical readiness, emotional readiness, and game_performance. The SEM confirmed our hypothesis and showed that players who were more physically and emotionally ready tended to perform better in games. 

Next, we build a second SEM model with only physical and emotional readiness and used extracted the predicted scores from this model. We then built a [dashboard](https://anoopnath703.shinyapps.io/readiness_report/) to track emotional readiness for each player over time. 

## Files

* [full_model_semopy.py](https://github.com/anath703/UVA_BASKETBALL_STRESS/blob/main/full_model_semopy.py)
  * This file creates the full SEM in Phyton using the Semopy package
* [readiness_only.R](https://github.com/anath703/UVA_BASKETBALL_STRESS/blob/main/readiness_only.R)
  * This file creates the readiness only model in R using the Lavaan package
* [readiness_report.Rmd](https://github.com/anath703/UVA_BASKETBALL_STRESS/blob/main/readiness_report.Rmd)
  * This creates a dashboard to visualize the readiness scores using Shiny App


