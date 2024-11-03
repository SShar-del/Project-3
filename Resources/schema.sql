CREATE TABLE pay_gap (
    id SERIAL PRIMARY KEY,             
    JobTitle VARCHAR(100),             
    Gender VARCHAR(10),                 
    Age INT,                      
    PerfEval VARCHAR(5),                
    Education VARCHAR(50),               
    Dept VARCHAR(100),                  
    Seniority VARCHAR(5),         
    BasePay INT,                         
    Bonus INT                            
);

