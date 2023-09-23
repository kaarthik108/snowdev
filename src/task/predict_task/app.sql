CREATE OR REPLACE TASK predict_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 1 * * * UTC'
  COMMENT = 'This task runs daily at 1am UTC'
AS
    call test_script(); -- call stored procedure
    