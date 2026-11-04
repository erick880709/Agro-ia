*** Settings ***
Library    DatabaseLibrary
Library    OperatingSystem

*** Variables ***
${DBName}    %{DB}
${DBHost}    %{HOST}
${DBPort}    %{PORT}
${DBUser}    %{USER}
${DBPass}    %{PASSWORD}
${KeyPath}   %{keyPath}

*** Keywords ***
Connect to database postgresql
    ${output}    Connect To Database    psycopg2    ${DBName}    ${DBUser}    ${DBPass}    ${DBHost}    ${DBPort}
    should be equal as strings    ${output}    None
    [Return]    ${output}
