% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/plot_weights.R
\name{plot_weights_scatter}
\alias{plot_weights_scatter}
\title{Scatterplots of weights}
\usage{
plot_weights_scatter(
  object,
  factors,
  view = 1,
  color_by = NULL,
  shape_by = NULL,
  dot_size = 1,
  name_color = "",
  name_shape = "",
  show_missing = TRUE,
  abs = FALSE,
  scale = TRUE,
  legend = TRUE
)
}
\arguments{
\item{object}{a trained \code{\link{MOFA}} object.}

\item{factors}{a vector of length two with the factors to plot. Factors can be specified either as a characters
using the factor names, or as numeric with the index of the factors}

\item{view}{character vector with the voiew name, or numeric vector with the index of the view to use. Default is the first view.}

\item{color_by}{specifies groups or values used to color the features. This can be either 
\itemize{
\item a character giving the same of a column in the feature metadata slot
\item a vector specifying the value for each feature. 
\item a dataframe with two columns: "feature" and "color"
}}

\item{shape_by}{specifies groups or values used to shape the features. This can be either 
\itemize{
\item a character giving the same of a column in the feature metadata slot
\item a vector specifying the value for each feature. 
\item a dataframe with two columns: "feature" and "shape"
}}

\item{dot_size}{numeric indicating dot size.}

\item{name_color}{name for color legend (usually only used if color_by is not a character itself)}

\item{name_shape}{name for shape legend (usually only used if shape_by is not a character itself)}

\item{show_missing}{logical indicating whether to include dots for which \code{shape_by} or \code{color_by} is missing}

\item{abs}{logical indicating whether to take the absolute value of the weights.}

\item{scale}{logical indicating whether to scale all weights from -1 to 1 (or from 0 to 1 if \code{abs=TRUE}).}

\item{legend}{logical indicating whether to add a legend to the plot (default is TRUE).}
}
\value{
Returns a \code{ggplot2} object
}
\description{
Scatterplot of the weights values for two factors
}
\details{
One of the first steps for the annotation of factors is to visualise and group/color them using known covariates such as phenotypic or clinical data.
This method generates a single scatterplot for the combination of two latent factors.
}
\examples{
# Using an existing trained model on simulated data
file <- system.file("extdata", "model.hdf5", package = "MOFA2")
model <- load_model(file)
plot_weights_scatter(model, factors = 1:2)
}
