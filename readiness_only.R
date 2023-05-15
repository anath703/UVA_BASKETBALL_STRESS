# Load libraries
library(lavaan)
library(semPlot)
library(lavaanPlot)
# Look at the dataset
Data<-read.csv('/Users/anoopnath/Desktop/MSDS/Capstone/stress_only.csv') #created in stress_only_data

# Define your model specification

model.specs <-'
# measurment model
physical_readiness =~ Physical_Performance_Capability  + Overall_Recovery + Overall_Stress_Score+   Muscular_Stress_Score +  Number_of_Sore_Areas
emotional_readiness=~ Mental_Performance_Capability  + Hours_of_Sleep_Previous_Night+ Lack_of_Activation_Score + Negative_Emotional_State_Score+ Emotional_Balance


# residual correlations

Negative_Emotional_State_Score ~~  Emotional_Balance
Mental_Performance_Capability ~~               Emotional_Balance
Mental_Performance_Capability ~~  Negative_Emotional_State_Score
Lack_of_Activation_Score ~~  Negative_Emotional_State_Score
#Countermovement_Depth_cm ~~           Muscular_Stress_Score
Muscular_Stress_Score ~~            Number_of_Sore_Areas
Physical_Performance_Capability ~~   Mental_Performance_Capability
Overall_Stress_Score ~~           Muscular_Stress_Score
Overall_Recovery ~~   Mental_Performance_Capability
physical_readiness~~emotional_readiness
'
fit <-sem(model= model.specs, data = Data)

## ------------------------------------------
## merge factor scores to original data.frame 
## and calculate percentiles
## ------------------------------------------
fscores <- lavPredict(fit)
idx <- lavInspect(fit, "case.idx")
## loop over factors to append factor scores to Data
for (fs in colnames(fscores)) {
  Data[idx, fs] <- fscores[ , fs]
}
# Calculate the percentiles
physical_readiness_ecdf <- ecdf(Data$physical_readiness)
Data$physical_readiness_percentile <- physical_readiness_ecdf(Data$physical_readiness) * 100

emotional_readiness_ecdf <- ecdf(Data$emotional_readiness)
Data$emotional_readiness_percentile <- emotional_readiness_ecdf(Data$emotional_readiness) * 100

## ------------------------------------------
#fitMeasures(fit)
summary(fit, standardized = TRUE, 
          fit.measures= TRUE, rsquare= TRUE
        )

#modificationindices(fit, sort= TRUE)
semPaths(object = fit,          whatLabels = "std",
         edge.label.cex = 1,
         what = "std",
         edge.color = "black")

lavaanPlot(model = fit, 
            edge_options = list(color = "grey"), coefs= TRUE, covs= TRUE, digits =3)

fitmeasures(fit, c('rmsea', 'srmr', 'cfi', 'rmsea.pvalue', 'aic' ))


##################Visualizations######################

# Load required libraries
library(ggplot2)

# Load the data (replace this line with your actual data loading method)
# Data <- read.csv("your_data_file.csv")

# Make sure the Date column is in the correct format
Data$Date <- as.Date(Data$Date)

# Function to plot readiness scores over time for a specific player
plot_readiness_scores <- function(player_id, data) {
  # Filter data for the specific player
  player_data <- data[data$Player_ID == player_id, ]
  
  # Check if there's data for the player
  if (nrow(player_data) == 0) {
    cat("No data available for Player_ID:", player_id)
    return(NULL)
  }
  
  # Create the plot
  plot <- ggplot(player_data, aes(x = Date)) +
    geom_line(aes(y = physical_readiness_percentile, color = "Physical Readiness")) +
    geom_line(aes(y = emotional_readiness_percentile, color = "Emotional Readiness")) +
    scale_color_manual(values = c("Physical Readiness" = "blue", "Emotional Readiness" = "red")) +
    labs(title = paste("Readiness Scores for Player", player_id),
         x = "Date",
         y = "Readiness Percentile",
         color = "Readiness Type") +
    theme_minimal()
  
  return(plot)
}

# Plot the readiness scores for a specific player (replace with desired Player_ID)
plot_readiness_scores(110, Data)


