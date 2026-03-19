# ------------------- User Customization Section -------------------

# Load necessary libraries
library(ggplot2)
library(readr)
library(dplyr)  # Data manipulation
library(tidyr)  # Pivoting data
library(RColorBrewer)  # For color palettes
library(fs)  # Directory creation

# Capture command-line arguments for versions
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("No version provided. Please pass version(s) as arguments.")
} else {
  version_list <- as.numeric(args)  # Capture multiple versions
}

# Iterate over versions and generate plots
for (version in version_list) {
# Define file paths based on dynamic version
code_files_path <- "C:/Users/md8w7/OneDrive University of Missouri/Desktop/ImportantFiles/Milestone4/Original"
results_folder <- file.path(code_files_path, paste0("Batch(", version, ")"), paste0("Results(", version, ")"))
data_csv_path <- file.path(results_folder, paste0("Fixed_Opex_Table_(", version, ").csv"))
plot_folder <- file.path(results_folder, paste0(version, "_PieStaticPlots_R"))
output_png_path <- file.path(plot_folder, "pie.png")

# Pie chart settings
dpi_value <- 300  # DPI for output quality (300 for print, 72 for web)
plot_width <- 8  # Plot width in inches
plot_height <- 6  # Plot height in inches

# Appearance customization
rotation_angle <- 45  # Rotate chart around the y-axis by 45 degrees
background_color <- "#E6E6FA"  # Light lavender background

# Labels for operational costs
labels_map <- c(
  "F1" = "Feedstock",
  "F2" = "Labor",
  "F3" = "Utility",
  "F4" = "Maintenance",
  "F5" = "Insurance"
)

# Title and text styling
plot_title <- "Operational Cost Breakdown"
font_family <- "Georgia"
title_size <- 18
title_margin_top <- 15
title_margin_bottom <- 15

# Border (frame) customization
frame_color <- "black"
frame_size <- 1
frame_margin <- 10

# ------------------- End of Customization Section -------------------

# Ensure the results folder exists
dir_create(plot_folder, recurse = TRUE)

# Remove the existing PNG if it exists
if (file.exists(output_png_path)) {
  file.remove(output_png_path)
  cat("Existing pie chart removed.\n")
}

# Read the CSV data
data <- read_csv(data_csv_path)

# Calculate averages dynamically, excluding 'Year'
averages <- data %>%
  select(-Year) %>%
  summarise(across(everything(), \(x) mean(x, na.rm = TRUE))) %>%
  pivot_longer(cols = everything(), names_to = "Label", values_to = "Value")

 # Replace F1-F5 labels with meaningful operational cost labels
averages$Label <- labels_map[averages$Label]

# Function to calculate percentages and trim values to one decimal
calculate_percentage <- function(df) {
  total <- sum(df$Value)
  df <- df %>%
    mutate(
      Percentage = (Value / total) * 100,
      RoundedValue = round(Value, 1)
    )
  return(df)
}

# Apply the percentage calculation function
averages <- calculate_percentage(averages)

# Separate displayable data (≥2%) and hidden data (<2%)
display_data <- averages %>% filter(Percentage >= 2)
hidden_data <- averages %>% filter(Percentage < 2)

# Use a color palette from RColorBrewer
palette <- brewer.pal(n = nrow(averages), name = "Set3")

# Create the pie chart with customization
pie_chart <- ggplot(display_data, aes(x = "", y = Value, fill = Label)) +
  geom_bar(stat = "identity", width = 1) +  # Pie slices
  coord_polar("y", start = rotation_angle * pi / 180) +  # Rotate chart
  theme_void() +  # Clean background
  ggtitle(plot_title) +  # Add title
  theme(
    plot.title = element_text(
      family = font_family, size = title_size, hjust = 0.9, vjust = 1,
      margin = margin(t = title_margin_top, b = title_margin_bottom)
    ),
    legend.position = "right",  # Legend on the right
    legend.text = element_text(size = 10, family = font_family),
    legend.title = element_blank(),  # No legend title
    plot.margin = margin(
      t = frame_margin, b = frame_margin,
      l = frame_margin, r = frame_margin
    ),
    plot.background = element_rect(
      fill = background_color, color = frame_color, size = frame_size
    )
  ) +
  scale_fill_manual(values = palette) +  # Apply color palette
  geom_text(
    aes(label = paste0(Label, ": ", round(Percentage, 1), "%")),
    position = position_stack(vjust = 0.5),
    size = 3, family = font_family, color = "black"
  )

# Save the pie chart as PNG
ggsave(output_png_path, pie_chart, width = plot_width, height = plot_height, dpi = dpi_value)

cat("Pie chart saved at:", output_png_path, "\n")
}