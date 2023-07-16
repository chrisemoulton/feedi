import datetime
import os
import time

import favicon
import feedparser
from flask import Flask, render_template


def create_app():
    app = Flask(__name__)
    app.config['feeds'] = load_hardcoded_feeds(app)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    @app.route("/")
    def hello_world():
        return render_template('base.html', entries=app.config['feeds'])

    # FIXME move somewhere else
    # TODO unit test this
    @app.template_filter('humanize')
    def humanize_date_filter(struct_time):
        "Pretty print a time.struct_time."

        delta = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(time.mktime(struct_time))

        if delta < datetime.timedelta(seconds=60):
            return f"{delta.seconds}s"
        elif delta < datetime.timedelta(hours=1):
            return f"{delta.seconds // 60}m"
        elif delta < datetime.timedelta(days=1):
            return f"{delta.seconds // 60 // 60 }h"
        elif delta < datetime.timedelta(days=8):
            return f"{delta.days}d"
        elif delta < datetime.timedelta(days=365):
            return time.strftime("%b %d", struct_time)
        return time.strftime("%b %d, %Y", struct_time)

    return app


def load_hardcoded_feeds(app):
    """
    Temporary setup to get some feed data for protoype development.
    Will eventually be moved to a db.
    """
    GOODREADS_TOKEN = os.getenv("GOODREADS_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    FEEDS = {
        "Apuntes Inchequeables": "https://facundoolano.github.io/feed.xml",
        "@grumpygamer": "https://mastodon.gamedev.place/@grumpygamer.rss",
        "lobste.rs": "https://lobste.rs/rss",
        "Github": f"https://github.com/facundoolano.private.atom?token={GITHUB_TOKEN}",
        "ambito.com": "https://www.ambito.com/rss/pages/home.xml",
        "Goodreads": f"https://www.goodreads.com/user/updates_rss/19714153?key={GOODREADS_TOKEN}"
    }

    entries = []
    for feed_name, url in FEEDS.items():
        app.logger.info('fetching %s', feed_name)
        feed = feedparser.parse(url)

        # TODO move somewhere else
        # FIXME this logic is not solid enough for the current options
        # also we need to more properly distinghuish between avatar and source icon
        avatar = None
        if 'image' in feed['feed']:
            avatar = feed['feed']['image']['href']
        elif 'webfeeds_icon' in feed['feed']:
            avatar = feed['feed']['webfeeds_icon']
        else:
            avatar = favicon.get(feed['feed']['link'])[0].url

        app.logger.debug('avatar is %s', avatar)

        for entry in feed['entries']:
            entries.append({'feed': feed_name,
                            'title': entry.get('title', '[no title]'),
                            'avatar': avatar,
                            'url': entry['link'],
                            'body': entry['summary'],
                            'date': entry['published_parsed']})

    entries.sort(key=lambda e: e['date'], reverse=True)
    return entries
