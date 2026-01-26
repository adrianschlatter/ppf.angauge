# Performance

On my MacMini, convert all images of 2025-08-20T2* (48 files) to numeric.


| test                                |   duration (s) | notes                             |
| ----------------------------------- | -------------- | --------------------------------- |
| 1 file at a time                    |           32   |                                   |
| all in 1 call                       |            1.5 | loading python was the bottleneck |
| 1 file at a time without matplotlib |           12   |                                   |
| all in 1 call without matplotlib    |            1.0 |                                   |
| 1 file w/o matplotlib, memmap       |            8.2 |                                   |
| 1 call w/o matplotlib, memmap       |            0.7 |                                   |
