-- Idempotent bootstrap for local/dev SQL Server: creates the "awa" database
-- and a scoped app login (separate from "sa"), matching the least-privilege
-- separation the old Postgres setup had via POSTGRES_USER: awa.
-- CHECK_POLICY is off deliberately - local dev convenience, never used for
-- a real environment.

IF DB_ID(N'awa') IS NULL
BEGIN
    CREATE DATABASE awa;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'mssql')
BEGIN
    CREATE LOGIN [mssql] WITH PASSWORD = '$(AWA_APP_PASSWORD)', CHECK_POLICY = OFF;
END
GO

USE awa;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'mssql')
BEGIN
    CREATE USER [mssql] FOR LOGIN [mssql];
    ALTER ROLE db_owner ADD MEMBER [mssql];
END
GO
