#!/usr/bin/python

import psycopg2
import config


def create_tables():
    """ create tables in the PostgreSQL database"""
    command = """
        CREATE TABLE users (
            user_id VARCHAR(255) NOT NULL,
            PRIMARY KEY (user_id )
        )
        """
    conn = None
    try:
        # read the connection parameters
        params = config.params
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # create table one by one
        # cur.execute("DROP TABLE subscriptions;")
        # cur.close()
        # conn.commit()
        # conn = psycopg2.connect(**params)
        # cur = conn.cursor()
        cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def insert_register(user_id):
    sql = """INSERT INTO users(user_id)
             VALUES(%s) RETURNING user_id;"""
    conn = None
    user_id = int(user_id)
    response = None
    try:
        # read the connection parameters
        params = config.params
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (user_id,))
        # get the generated id back
        response = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return response


def get_registers():
    conn = None
    result = []
    try:
        # read the connection parameters
        params = config.params
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id FROM users")
        row = cur.fetchone()

        while row is not None:
            result.append(row[0])
            row = cur.fetchone()

        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return result
