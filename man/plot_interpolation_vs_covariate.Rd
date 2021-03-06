% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/mefisto.R
\name{plot_interpolation_vs_covariate}
\alias{plot_interpolation_vs_covariate}
\title{Plot interpolated factors versus covariate (1-dimensional)}
\usage{
plot_interpolation_vs_covariate(
  object,
  covariate = 1,
  factors = "all",
  only_mean = TRUE,
  show_observed = TRUE
)
}
\arguments{
\item{object}{a trained \code{\link{MOFA}} object using MEFISTO.}

\item{covariate}{covariate to use for plotting}

\item{factors}{character vector with the factors names, or numeric vector indicating the indices of the factors to use}

\item{only_mean}{show only mean or include uncertainties?}

\item{show_observed}{include observed factor values as dots on the plot}
}
\value{
Returns a \code{ggplot2} object
}
\description{
make a plot of interpolated covariates versus covariate
}
\details{
to be filled
}
\examples{
# Using an existing trained model
file <- system.file("extdata", "MEFISTO_model.hdf5", package = "MOFA2")
model <- load_model(file)
model <- interpolate_factors(model, new_values = seq(0,1.1,0.1))
plot_interpolation_vs_covariate(model, covariate = "time", factors = "all")
}
