#!/usr/bin/env python

"""Scraper for a Facebook group.
   David Mendez <hello@davidemdot.com>"""

import csv
import datetime
import json
import sys
import time
import urllib2


def request(url):
    """Try to open and read an URL.
    """
    req = urllib2.Request(url)

    while True:
        try:
            resp = urllib2.urlopen(req)
            return resp.read()
        except urllib2.URLError, err:
            if hasattr(err, 'code') and err.code == 400:
                print '*** Please check the group id and the access token.\n'
                raise err
            print '*** %s. Retrying...' % err
            time.sleep(5)


def get_group_data():
    """Build the URL to ask for threads and comments data.
    """
    url = 'https://graph.facebook.com/v2.3/%s/feed?fields=' % GROUP_ID
    url += 'id,permalink_url,created_time,from,message,type,link,'
    url += 'likes.limit(0).summary(true),comments{id,created_time,from,'
    url += 'message,comment_count,like_count,attachment,comments{id,'
    url += 'created_time,from,message,like_count,attachment}}'
    url += '&limit=100&access_token=%s' % ACCESS_TOKEN

    return json.loads(request(url))


def format_string(text):
    """Format a string in a good way.
    """
    if text is None:
        return ''

    return ' '.join(
        text.translate({
            0x2018: 0x27,
            0x2019: 0x27,
            0x201C: 0x22,
            0x201D: 0x22,
            0xA0: 0x20,
            0xA: 0x20,
            0xD: 0x20
        }).encode('utf-8').split())


def format_date(date, short=True):
    """Format a date in the selected way.
    """
    return date.strftime('%H:%M:%S') if short else \
        date.strftime('%Y-%m-%d %H:%M:%S')


def process_post(post, parent=''):
    """Process the data from a thread or a comment.
    """
    post_id = post.get('id', '-1')
    date = '' if 'created_time' not in post else datetime.datetime.strptime(
        post['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    author = format_string(post['from'].get('name'))
    message = format_string(post.get('message'))

    # If it's a thread
    if parent == '':
        parent = format_string(post.get('permalink_url'))
        likes = 0 if 'likes' not in post else \
            post['likes']['summary']['total_count']
        comments = 0 if 'comments' not in post else \
            len(post['comments']['data'])
        kind = format_string(post.get('type'))

        link = format_string(post.get('link'))
        if link != '':
            if message != '':
                message += ' '
            message += '[' + link + ']'

    # If it's a comment
    else:
        likes = post.get('like_count', 0)
        comments = post.get('comment_count', 0)
        kind = 'comment' if 'comment_count' in post else 'subcomment'

        if 'attachment' in post:
            kind += '_' + format_string(post['attachment'].get('type'))

    return (str(post_id),
            str(parent),
            format_date(date, False),
            author,
            message,
            kind,
            likes,
            comments)


def get_comments(thread, output):
    """Get all the comments and subcomments from a thread.
    """
    num_comments = 0
    next_page = True
    comments = thread.get('comments')

    while next_page and comments is not None:
        for comment in comments.get('data', []):
            output.writerow(process_post(comment, thread['id']))

            next_subpage = True
            subcomments = comment.get('comments')

            while next_subpage and subcomments is not None:
                for subcomment in subcomments['data']:
                    output.writerow(process_post(subcomment, comment['id']))
                    num_comments += 1
                if 'paging' in subcomments and 'next' in subcomments['paging']:
                    subcomments = json.loads(request(
                        subcomments['paging']['next']))
                else:
                    next_subpage = False

            num_comments += 1

        if 'paging' in comments and 'next' in comments['paging']:
            comments = json.loads(request(comments['paging']['next']))
        else:
            next_page = False

    return num_comments


def write_csv():
    """Write the categorized data in a CSV file.
    """
    with open('%s_group.csv' % GROUP_ID, 'wb') as file_name:
        output = csv.writer(file_name)
        output.writerow(['id',
                         'ref',
                         'date',
                         'author',
                         'message',
                         'kind',
                         'likes',
                         'comments'])

        next_page = True
        end = False
        num_threads = 0
        num_comments = 0
        threads = get_group_data()

        while next_page and not end:
            for thread in threads['data']:
                output.writerow(process_post(thread))

                num_comments += get_comments(thread, output)
                num_threads += 1

                if num_threads == MAX_THREADS:
                    end = True
                    break
                elif num_threads % 50 == 0:
                    print '(%s) %s threads and %s comments processed' % \
                        (format_date(datetime.datetime.now()),
                         num_threads, num_comments)

            if 'paging' in threads and not end:
                threads = json.loads(request(threads['paging']['next']))
            else:
                next_page = False

        return (num_threads, num_comments)


def main():
    """Main method.
    """
    print '\n(%s) Getting the last %d threads from Facebook group #%s\n' % \
        (format_date(datetime.datetime.now()), MAX_THREADS, GROUP_ID)

    num_threads, num_comments = write_csv()

    print '\n(%s) That\'s all! %s threads and %s comments in total\n' % \
        (format_date(datetime.datetime.now()), num_threads, num_comments)


if __name__ == '__main__':
    try:
        GROUP_ID = str(int(sys.argv[1]))
        ACCESS_TOKEN = sys.argv[2]
        MAX_THREADS = int(sys.argv[3]) if len(sys.argv) > 3 else 250

    except (IndexError, ValueError), err:
        print '\nError: %s' % err
        print 'Usage: %s <group_id> <access_token> [max_threads]' % sys.argv[0]
        sys.exit(2)

    main()
