args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) > 0) {
  script_path <- normalizePath(sub("^--file=", "", file_arg[[1]]))
  project_root <- normalizePath(file.path(dirname(script_path), "..", ".."))
} else {
  project_root <- normalizePath(getwd())
}
figures_dir <- file.path(project_root, "figures", "final")
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

message("Project root: ", project_root)
message("Replace this template with project-specific R analysis.")
