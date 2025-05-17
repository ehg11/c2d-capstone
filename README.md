# C2D Profiling Capstone - Edward Hwang

This project contains files relevant to the profiling project for the C2D and miniC2D knowledge compilers. Only the files relevant for analysis are included. 

The actual `perf` reports and outputs from running each compiler (which are relevant to the analysis) can be found at this [Google Drive link](https://drive.google.com/drive/folders/1Z-k7WipKieLs6COX4Df1cy1BvDyvSVVS?usp=sharing). To run the code in each `analyze_times.ipynb` Jupyter Notebook, be sure to following the following file structure (existing directories omitted). 

```
.
├── c2d-analysis
│   ├── perf-report
│   └── stdout
└── miniC2D-analysis
    ├── perf-report
    └── stdout
```

Python scripts used to obtain the `perf` reports and outputs can be found in `c2d-analysis/scripts` and `miniC2D-analysis/scripts`. 

