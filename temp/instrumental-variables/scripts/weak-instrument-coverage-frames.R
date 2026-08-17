#!/usr/bin/env Rscript
# Frames for the weak-instrument coverage animation.
suppressMessages({library(ggplot2); library(patchwork)})

set.seed(20260804)
yale_blue <- "#00356B"
miss_col  <- "#B23A2E"
ggplot2::theme_set(ggplot2::theme_minimal(base_size = 11))

outdir <- commandArgs(trailingOnly = TRUE)[1]
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

n     <- 500     # observations per simulated study
S     <- 8000    # simulated studies per frame
beta  <- 1       # true effect
rho   <- 0.95    # endogeneity: corr(u, v), a near-worst case
n_ci  <- 60      # intervals drawn in the left panel

# One set of shocks, reused across every frame. Only the first-stage
# coefficient changes, so each interval visibly tightens instead of being
# redrawn at random.
Z <- matrix(rnorm(n * S), n, S)
V <- matrix(rnorm(n * S), n, S)
U <- rho * V + sqrt(1 - rho^2) * matrix(rnorm(n * S), n, S)
Szz <- colSums(Z^2)

Fgrid <- c(2, 2.5, 3, 4, 5, 6.5, 8, 10, 13, 17, 22, 30, 40, 55, 75, 100, 130, 170)

fit_frame <- function(Fval) {
  p   <- sqrt((Fval - 1) / n)
  D   <- p * Z + V
  Y   <- beta * D + U
  Szd <- colSums(Z * D)
  b   <- colSums(Z * Y) / Szd
  res <- Y - D * matrix(b, n, S, byrow = TRUE)
  se  <- sqrt(colSums(Z^2 * res^2) / Szd^2)          # HC0, just-identified
  # realized homoskedastic first-stage F
  pf   <- Szd / Szz
  fres <- D - Z * matrix(pf, n, S, byrow = TRUE)
  Fobs <- pf^2 * Szz / (colSums(fres^2) / (n - 2))
  list(b = b, se = se, lo = b - 1.96 * se, hi = b + 1.96 * se,
       coverage = mean(b - 1.96 * se <= beta & b + 1.96 * se >= beta),
       Fbar = mean(Fobs))
}

frames <- lapply(Fgrid, fit_frame)

idx   <- sample(S, n_ci)
order_by <- rank(frames[[length(frames)]]$b[idx], ties.method = "first")
cov_df <- data.frame(
  Fbar     = vapply(frames, `[[`, numeric(1), "Fbar"),
  coverage = vapply(frames, `[[`, numeric(1), "coverage")
)
xlim_ci <- c(-0.6, 3.2)
xr <- range(cov_df$Fbar)

for (i in seq_along(frames)) {
  fr <- frames[[i]]
  ci <- data.frame(
    row  = order_by,
    est  = fr$b[idx],
    lo   = pmax(fr$lo[idx], xlim_ci[1] - 1),
    hi   = pmin(fr$hi[idx], xlim_ci[2] + 1),
    hit  = ifelse(fr$lo[idx] <= beta & fr$hi[idx] >= beta, "covers", "misses")
  )

  p_ci <- ggplot(ci, aes(y = row, colour = hit)) +
    geom_vline(xintercept = beta, linetype = "dashed", colour = "grey35") +
    geom_segment(aes(x = lo, xend = hi, yend = row), linewidth = 0.45, alpha = 0.9) +
    geom_point(aes(x = est), size = 0.85) +
    scale_colour_manual(values = c(covers = yale_blue, misses = miss_col),
                        guide = "none") +
    coord_cartesian(xlim = xlim_ci, expand = FALSE) +
    labs(x = expression("2SLS estimate and conventional 95% interval ("*beta*" = 1)"),
         y = NULL,
         subtitle = sprintf("%d of %d intervals shown", n_ci, S)) +
    theme(axis.text.y = element_blank(), panel.grid.major.y = element_blank(),
          panel.grid.minor = element_blank(),
          plot.subtitle = element_text(size = 8.5, colour = "grey40"))

  p_cov <- ggplot(cov_df, aes(Fbar, coverage)) +
    geom_hline(yintercept = 0.95, linetype = "dashed", colour = "grey35") +
    geom_vline(xintercept = 10, linetype = "dotted", colour = "grey55") +
    geom_vline(xintercept = 104.7, linetype = "dotted", colour = yale_blue) +
    annotate("text", x = 10, y = 0.792, label = "F = 10", size = 2.9,
             colour = "grey45", hjust = 1.1) +
    annotate("text", x = 104.7, y = 0.792, label = "F = 104.7", size = 2.9,
             colour = yale_blue, hjust = 1.1) +
    (if (i > 1) geom_line(data = cov_df[seq_len(i), ], colour = yale_blue, linewidth = 0.8) else NULL) +
    geom_point(data = cov_df[seq_len(i), ], colour = yale_blue, size = 1.5) +
    geom_point(data = cov_df[i, ], colour = miss_col, size = 3.2) +
    scale_x_log10(limits = xr, breaks = c(2, 5, 10, 25, 50, 100)) +
    scale_y_continuous(limits = c(0.78, 1), breaks = seq(0.80, 1, 0.05),
                       labels = scales::percent_format(accuracy = 1)) +
    labs(x = "Mean first-stage F (log scale)",
         y = "Coverage of the nominal 95% interval",
         subtitle = " ") +
    theme(panel.grid.minor = element_blank())

  ttl <- sprintf(
    "First-stage F \u2248 %.0f      Coverage of the nominal 95%% interval: %.1f%%",
    fr$Fbar, 100 * fr$coverage)

  pw <- (p_ci | p_cov) +
    plot_annotation(
      title = ttl,
      subtitle = sprintf(
        "Just-identified IV, n = %d, corr(u, v) = %.2f. Only the first-stage coefficient changes across frames.",
        n, rho),
      theme = theme(
        plot.title = element_text(face = "bold", size = 12.5, colour = yale_blue),
        plot.subtitle = element_text(size = 8.8, colour = "grey40"))
    )

  ggsave(file.path(outdir, sprintf("frame_%02d.png", i)), pw,
         width = 8.2, height = 3.6, dpi = 110, bg = "white")
}

write.csv(cov_df, file.path(outdir, "coverage.csv"), row.names = FALSE)
cat("frames:", length(frames), "\n")
print(round(cov_df, 3))
