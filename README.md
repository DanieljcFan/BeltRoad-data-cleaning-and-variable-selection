# BeltRoad-data-cleaning-and-variable-selection
A example of data cleaning and variable selection

original data: 
 - report.rda(Y for regression): each row represents a report of certain corporation at certain time, with following variables:

|     Variables | type      | note                                          |
|--------------:|-----------|-----------------------------------------------|
| ...           | ...       | ...                                           |
| corp_name     | factor    | name of corporations                          |
| report_period | character | time of report, format YYYY-mm-dd             |
| ...           | ...       | ...                                           |
| 净利润(netin) | numeric   | net income of corporation at this time period |
| ...           | ...       | ...                                           |

 - cement.csv(X for regression): records of matker variables. Due to different frequency a lot of NA exists.

WorkExample.r: code of data analysis process
 - First reorganize data to be neat and structured.
 - variable selection for regression:
   - forward selection based on marginal R-square to avoid p>n
   - set threshold for vif to avoid multicollinearity。

result：
 - model.txt summary of regression model in text
 - fitted.csv compare of fitted value and true value
 - fitted.jpeg visualization of compare


