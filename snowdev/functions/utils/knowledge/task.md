This is the definition to create tasks in snowflake.

CREATE OR REPLACE TASK sample_task -- this the task name and folder name
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 1 * * * UTC' -- this is the schedule
  COMMENT = 'This task runs daily at 1am UTC' -- add comment
    call test_script(); -- call stored procedure or sql statement

-- alter task sample_task resume; -- to resume the task if asked to suspend else do not run this command