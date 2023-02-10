
import re
import sqlite3
from getTitle import get_title
import processMetadata
from time import strftime, localtime
from env import *
from log import logger


def upsert_series_record(conn, series_id, subject_id, update_success, series_name, bangumi_name):
    """
    插入或更新数据记录
    :param conn: 数据库连接
    :param table: 表名
    :param series_id: komga id
    :param subject_id: bangumi id
    :param update_success: 更新是否成功
    :param series_name: komga名称
    :param refresh_time: 刷新时间
    :param bangumi_name: bangumi名称
    """
    c = conn.cursor()
    # 0 (false) and 1 (true)
    c.execute("INSERT OR REPLACE INTO refreshed_series (series_id,subject_id,update_success,series_name,bangumi_name,refresh_time) VALUES (?,?,?,?,?,?)",
                (series_id, subject_id, update_success, series_name, bangumi_name, strftime('%Y-%m-%d %H:%M:%S', localtime()),))
    conn.commit()


def upsert_book_record(conn, book_id, subject_id, update_success, book_name):
    c = conn.cursor()
    # 0 (false) and 1 (true)
    c.execute("INSERT OR REPLACE INTO refreshed_books (book_id,subject_id,update_success,book_name,refresh_time) VALUES (?,?,?,?,?)",
                (book_id, subject_id, update_success, book_name, strftime('%Y-%m-%d %H:%M:%S', localtime()),))
    conn.commit()


def refresh_metadata(force_refresh_list=[]):
    '''
    Refresh book series metadata
    '''
    env = InitEnv()

    komga = env.komga
    all_series = env.all_series

    # Create a connection to the sqlite database /// @Inervo: Is it necessary???
    conn = sqlite3.connect("recordsRefreshed.db")
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS refreshed_series (series_id text primary key,subject_id text ,update_success BOOLEAN,series_name text,bangumi_name text,refresh_time text )''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS refreshed_books (book_id text primary key,subject_id text ,update_success BOOLEAN,book_name text,refresh_time text )''')

    # Loop through each book series
    for series in all_series:
        series_id = series['id']
        series_name = series['name']

        force_refresh_flag = series_id in force_refresh_list
        # Skip the series if it's not in the force refresh list
        if len(force_refresh_list) > 0 and not force_refresh_flag:
            continue

        # Check if the series has already been refreshed
        if c.execute("SELECT * FROM refreshed_series WHERE series_id=? AND update_success=1", (series_id,)).fetchone() and not force_refresh_flag:
            subject_id = c.execute(
                "SELECT subject_id FROM refreshed_series WHERE series_id=?", (series_id,)).fetchone()[0]
            refresh_book_metadata(komga, subject_id,
                                    series_id, conn, force_refresh_flag)
            continue

        # Get the subject id from the Correct Bgm Link (CBL) if it exists
        subject_id = None
        for link in series['metadata']['links']:
            if link['label'].lower() == "cbl": ## TODO @Inervo: retrieve bedetheque metadata here
                subject_id = link['url'].split("/")[-1]
                # Get the metadata for the series from bangumi
                metadata = bgm.get_subject_metadata(subject_id)
                break

        # Use the bangumi API to search for the series by title on komga
        # if subject_id == None:
        #     title = get_title(series_name)
        #     if title == None:
        #         logger.warning("Failed to update series " +
        #                        series_name+": None")
        #         upsert_series_record(conn, series_id, subject_id,
        #                              0, series_name, "None")
        #         continue
        #     search_results = bgm.search_subjects(title)
        #     if len(search_results) > 0:
        #         subject_id = search_results[0]['id']
        #         metadata = search_results[0]
        #     else:
        #         logger.warning("Failed to update series " +
        #                        series_name+": no subject in bangumi")
        #         upsert_series_record(conn, series_id, subject_id,
        #                              0, series_name, "None")
        #         continue

        komga_metadata = processMetadata.setKomangaSeriesMetadata(
            metadata, series_name)

        if(komga_metadata.isvalid == False):
            logger.warning("Failed to update series " + series_name)
            upsert_series_record(conn, series_id, subject_id,
                                    0, series_name, komga_metadata.title)
            continue

        series_data = {
            "status": komga_metadata.status,
            "summary": komga_metadata.summary,
            "publisher": komga_metadata.publisher,
            "genres": komga_metadata.genres,
            "tags": komga_metadata.tags,
            "title": komga_metadata.title,
            "alternateTitles": komga_metadata.alternateTitles,
            "ageRating": komga_metadata.ageRating,
            "links": komga_metadata.links,
            "totalBookCount": komga_metadata.totalBookCount
        }

        # Update the metadata for the series on komga
        isSuccessed = komga.update_series_metadata(series_id, series_data)
        if(isSuccessed):
            logger.info("Successfully update series " + series_name)
            # Update the refreshed series in the sqlite database
            upsert_series_record(conn, series_id, subject_id,
                                    1, series_name, komga_metadata.title)
        else:
            logger.warning("Failed to update series " + series_name)
            upsert_series_record(conn, series_id, subject_id,
                                    0, series_name, komga_metadata.title)
            continue

        refresh_book_metadata(komga, subject_id,
                                series_id, conn, force_refresh_flag)


def getNumber(s):
    # TODO 数字匹配，包括：I、一、1、①
    # Define the pattern to match decimal numbers in the format of "xx.xx"
    pattern = r"\d+\.\d"
    # e.g. 16-5
    s = s.replace('-', '.').replace('_', '.')
    # Use the `re.findall` function to search for all occurrences of the pattern in the input string
    numbers = re.findall(pattern, s)
    # If no decimal numbers are found, change the pattern to match integer numbers
    if not numbers:
        pattern = r"\d+"
        numbers = re.findall(pattern, s)

    # Return the list of found numbers
    return numbers


def refresh_book_metadata(komga, subject_id, series_id, conn, force_refresh_flag):
    '''
    Refresh Book Metadata
    '''
    if subject_id == None:
        return
    # # Get the related subjects for the series from bangumi
    # related_subjects = [subject for subject in bgm.get_related_subjects(
    #     subject_id) if subject['relation'] == "单行本"]

    # # Get the number for each related subject by finding the last number in the name or name_cn field
    # subjects_numbers = []
    # for subject in related_subjects:
    #     numbers = getNumber(subject['name'] + subject['name_cn'])
    #     try:
    #         subjects_numbers.append(
    #             float(numbers[-1]) if numbers else float(1))
    #     except ValueError:
    #         logger.warning("Failed to extract number ")

    # Get all books in the series on komga
    books = komga.get_series_books(series_id)

    # Loop through each book in the series on komga
    for book in books['content']:
        book_id = book['id']
        book_name = book['name']

        c = conn.cursor()
        if c.execute("SELECT * FROM refreshed_books WHERE book_id=? AND update_success=1", (book_id,)).fetchone() and not force_refresh_flag:
            continue

        # get nunmber from book name
        try:
            book_number = float(getNumber(book_name)[-1])
        except:
            book_number = float(1)
        ep_flag = True
        # Update the metadata for the book if its number matches a related subject number
        for i, number in enumerate(subjects_numbers):
            if book_number == number:
                ep_flag = False
                # Get the metadata for the book from bangumi
                book_metadata = processMetadata.setKomangaBookMetadata(
                    related_subjects[i]['id'], number, book_name)
                if(book_metadata.isvalid == False):
                    logger.warning("Failed to update book " + book_name)
                    upsert_book_record(
                        conn, book_id, related_subjects[i]['id'], 0, book_name)
                    break

                book_data = {
                    "authors": book_metadata.authors,
                    "summary": book_metadata.summary,
                    "tags": book_metadata.tags,
                    "title": book_metadata.title,
                    "isbn": book_metadata.isbn,
                    "number": book_metadata.number,
                    "links": book_metadata.links,
                    "releaseDate": book_metadata.releaseDate,
                    "numberSort": book_metadata.numberSort
                }

                # Update the metadata for the series on komga
                isSuccessed = komga.update_book_metadata(
                    book_id, book_data)
                if(isSuccessed):
                    logger.info("Successfully update book " + book_name)
                    upsert_book_record(
                        conn, book_id, related_subjects[i]['id'], 1, book_name)
                else:
                    logger.warning("Failed to update book " + book_name)
                    upsert_book_record(
                        conn, book_id, related_subjects[i]['id'], 0, book_name)
                break
        # Modify the serial number of `chapter`
        if ep_flag:
            book_data = {
                "number": book_number,
                "numberSort": book_number
            }
            komga.update_book_metadata(
                book_id, book_data)


refresh_metadata(FORCE_REFRESH_LIST)
