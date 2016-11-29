#!/usr/bin/env python

"""Scraper for a Facebook group."""

__author__ = "David Mendez"
__email__ = "hello@davidemdot.com"


import csv
import datetime
import json
import sys
import urllib
import urllib2


def request(url):
    """Try to open and read an URL.
    """
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req).read()

    except urllib2.HTTPError, err:
        if err.code == 400:
            print '\nError. Please, check the group id and the access token.\n'
        sys.exit(2)

    return response

def get_group_data():
    """Build the URL to ask for threads and comments data.
    """
    url = 'https://graph.facebook.com/v2.3/%s/feed?fields=' % GROUP_ID
    url += 'id,created_time,from,message,type,likes.limit(0).summary(true),'
    url += 'link,name,comments{id,created_time,from,message,comment_count,'
    url += 'like_count,attachment,comments{id,created_time,from,message,'
    url += 'like_count,attachment}}&limit=100&access_token=%s' % ACCESS_TOKEN

    return json.loads(request(url))

def format_string(text):
    """ Format a string in a good way.
    """
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

def format_date(date, style):
    """Format a date in the selected way.
    """
    if style == 0:
        return date.strftime('%Y-%m-%d %H:%M:%S')
    elif style == 1:
        return date.strftime('%H:%M:%S')

def extract_fb_url(url):
    """Remove the referral URL from Facebook in a link.
    """
    url = url.encode('ascii')
    url = url[int(url.find('l.php?u='))+8:int(url.find('&h='))]

    return urllib.unquote(url)

def process_post(post, parent_id=''):
    """Process the data from a thread or a comment.
    """
    post_id = post['id']
    date = datetime.datetime.strptime(
        post['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    author = format_string(post['from']['name'])
    message = '' if 'message' not in post.keys() else \
        format_string(post['message'])

    # If it's a thread
    if parent_id == '':
        parent_id = 'https://www.facebook.com/groups/%s/permalink/%s' % \
            (GROUP_ID, post_id[len(GROUP_ID)+1:])
        likes = post['likes']['summary']['total_count']
        comments = 0 if 'comments' not in post.keys() else \
            len(post['comments']['data'])
        kind = post['type']

        if kind != 'status':
            if 'name' in post.keys():
                link = format_string(post['name'] + ': ' + post['link'])
            else:
                link = format_string(post['link'])
        else:
            link = ''

    # If it's a comment
    else:
        likes = post['like_count']
        comments = 0 if 'comment_count' not in post.keys() else \
            post['comment_count']
        kind = 'comment'
        link = ''

        if 'attachment' in post.keys():
            if 'type' in post['attachment']:
                kind = post['attachment']['type']

            if kind.startswith('video'):
                kind = 'video'
            elif kind.endswith('image_share'):
                kind = 'image'

            link = '' if 'title' not in post['attachment'] else \
                format_string(post['attachment']['title']) + ': '
            link += '' if 'url' not in post['attachment'] else \
                extract_fb_url(format_string(post['attachment']['url']))

    return (str(post_id),
            str(parent_id),
            format_date(date, 0),
            author,
            message,
            kind,
            link,
            likes,
            comments)

def get_comments(thread, output):
    """Get all the comments and subcomments from a thread.
    """
    num_comments = 0
    next_page = True
    comments = None if 'comments' not in thread.keys() else thread['comments']

    while next_page and comments is not None:
        for comment in comments['data']:
            output.writerow(process_post(comment, thread['id']))

            next_subpage = True
            subcomments = None if 'comments' not in comment else \
                comment['comments']

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
                         'parent_id',
                         'date',
                         'author',
                         'message',
                         'kind',
                         'link',
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
                        (format_date(datetime.datetime.now(), 1),
                         num_threads, num_comments)

            if 'paging' in threads.keys() and not end:
                threads = json.loads(request(threads['paging']['next']))
            else:
                next_page = False

        return (num_threads, num_comments)

def main():
    """Main method.
    """
    print '\n(%s) Getting the last %d threads from FaceBook group #%s\n' % \
        (format_date(datetime.datetime.now(), 1), MAX_THREADS, GROUP_ID)

    num_threads, num_comments = write_csv()

    print '\n(%s) That\'s all! %s threads and %s comments in total\n' % \
        (format_date(datetime.datetime.now(), 1), num_threads, num_comments)


if __name__ == '__main__':
    try:
        GROUP_ID = str(int(sys.argv[1]))
        ACCESS_TOKEN = sys.argv[2]
        MAX_THREADS = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    except (IndexError, ValueError), err:
        print '\nError: %s' % err
        print 'Usage: %s <group_id> <access_token> [max_threads]' % sys.argv[0]
        sys.exit(2)

    main()
