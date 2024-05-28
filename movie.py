#!/bin/env python

import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup as BS
import json
import re
from fuzzywuzzy import process
from unidecode import unidecode as ud
from youtubesearchpython import VideosSearch as VS
import asyncio
import pandas as pd

tspdt_rankings = pd.read_excel('/home/emre/.local/bin/tspdt_rankings.xlsx')

def nt(txt):
    return ud(str(txt).lower().replace(' ', '-'))

def grt(m, y):
    s = ud(str(m).lower().replace('-', '_'))
    return [f'https://www.rottentomatoes.com/m/{s}', f'https://www.rottentomatoes.com/m/{s}_{y}']

async def ft(u, s):
    async with s.get(u) as r:
        return await r.text()

async def gras(m, y, s):
    if nt(m) == 'mirror':
        return '91'
    us = grt(m, y)

    async def fs(u):
        t = await ft(u, s)
        sp = BS(t, 'html.parser')
        sc = sp.find('script', {'id': 'scoreDetails'})
        if sc:
            d = json.loads(sc.string)
            v = d['scoreboard']['audienceScore'].get('value')
            if v and v != 0:
                return str(v).split('/')[0]

    ss = await asyncio.gather(*(fs(u) for u in us))
    return next((score for score in ss if score is not None), "N/A")

async def gtr(m):
    try:
        bm = process.extractOne(m, tspdt_rankings['title'])[0]
        return tspdt_rankings[tspdt_rankings['title'] == bm]['rank'].values[0]
    except:
        return "Error"

async def glr(m, y, s):
    try:
        mn = nt(m)
        mn = m.lower().replace(' ', '-')
        if y:
            mn += f'-{y}'
        u = f'https://letterboxd.com/film/{mn}/'
        async with s.get(u) as r:
            if r.status != 200:
                mn = m.lower().replace(' ', '-')
                u = f'https://letterboxd.com/film/{mn}/'
                async with s.get(u) as r2:
                    t = await r2.text()
            else:
                t = await r.text()
        sp = BS(t, 'html.parser')
        mt = sp.find('meta', attrs={'name': 'twitter:data2'})
        if mt:
            rt = mt['content']
            ro5 = float(rt.split(' ')[0])
            return ro5 * 2
        else:
            return "N/A"
    except:
        return "Error"

async def gmus(m, y, s):
    try:
        mn = nt(m)
        u = f"https://www.metacritic.com/movie/{mn}"
        h = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.metacritic.com'}
        us = [u]
        if y:
            us.insert(0, f"{u}-{y}")
        for u in us:
            async with s.get(u, headers=h) as r:
                if r.status == 200:
                    t = await r.text()
                    sp = BS(t, 'html.parser')
                    uss = sp.select_one('div.c-productScoreInfo_scoreNumber div.c-siteReviewScore span')
                    if uss:
                        sc = uss.get_text(strip=True)
                        return sc
    except:
        return None

async def st(ctx, m, y, s):
    try:
        q = f"{m} x265 bluray 1080p 10bit {y}" if y else f"{m} x265"
        q = q.replace(' ', '+')
        su = f'https://1337x.to/search/{q}/1/'
        async with s.get(su) as r:
            sp = await r.text()
        mm = re.findall(r"torrent/[0-9]{7}/[a-zA-Z0-9?%-]*/", sp)
        hc = []
        sg = []
        for ma in mm[:5]:
            mu = f"https://1337x.to/{ma}"
            async with s.get(mu) as r:
                mp = await r.text()
            hm = re.search(r"<strong>Infohash :</strong> <span>([a-zA-Z0-9]*)</span>", mp)
            sm = re.search(r"\b\d+(\.\d+)?\sGB\b", mp)
            if hm:
                hc.append(hm.group(1))
            if sm:
                sg.append(sm.group(0))
        if not hc:
            await ctx.send(f"No hash codes found for {m}")
            return
        embed = discord.Embed(title=f"Torrents for {m}", color=discord.Color.blue())
        for i, (h, s) in enumerate(zip(hc, sg)):
            ht = f"Hash {i + 1} - {s}"
            embed.add_field(name=ht, value=h, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def main():
    session = aiohttp.ClientSession()

    @bot.command()
    async def m(ctx, *, movie_name):
        try:
            nmn = nt(movie_name)
            url = "http://www.omdbapi.com/?apikey=98e54415&t=" + nmn.replace(' ', '+')
            async with session.get(url) as r:
                data = await r.json()
            if data['Response'] == 'False':
                await ctx.send(f"Movie {movie_name} not found.")
                return
            else:
                year = None
            if data['Response'] == 'True':
                year = data['Year'].split('–')[0]
            rta = await gras(nmn, y=year, s=session)
            mu = await gmus(nmn, y=year, s=session)
            lr = await glr(nmn, y=year, s=session)
            plot = data['Plot']
            title = data['Title']
            year = data['Year'].split('-')[0]
            genre = data['Genre']
            director = data['Director']
            actors = data['Actors']
            imdb_rating = str(int(float(data['imdbRating']) * 10))
            imdb_votes = data['imdbVotes']
            rotten_tomatoes = 'N/A'
            for rating in data['Ratings']:
                if rating['Source'] == 'Rotten Tomatoes':
                    rotten_tomatoes = rating['Value'].replace('%', '')
            metacritic = 'N/A'
            for rating in data['Ratings']:
                if rating['Source'] == 'Metacritic':
                    metacritic = rating['Value'].split('/')[0]
            lro100 = str(round(float(lr) * 10)) if lr != "N/A" else "N/A"
            tr = await gtr(nmn)
            ytl = VS(f'{title} {year} trailer', limit=1).result()['result'][0]['link'] if VS(f'{title} {year} trailer', limit=1).result()['result'] else None
            scores = [int(imdb_rating) if imdb_rating else None,
                      int(rotten_tomatoes.split('/')[0]) if rotten_tomatoes != "N/A" and '/' in rotten_tomatoes else None,
                      int(rta) if rta != "N/A" else None,
                      int(metacritic) if metacritic != "N/A" else None,
                      int(lro100) if lro100 != "N/A" else None,
                      int(mu) if mu != "N/A" else None]
            vs = [s for s in scores if s is not None]
            avg = round(sum(vs) / len(vs)) if vs else "N/A"
            embed = discord.Embed(title=title, url=ytl, description=plot, color=discord.Color.blue())
            embed.add_field(name="Year", value=year, inline=True)
            embed.add_field(name="Genre", value=genre, inline=True)
            embed.add_field(name="Director", value=director, inline=True)
            embed.add_field(name="Actors", value=actors, inline=True)
            embed.add_field(name="IMDB", value=imdb_rating, inline=True)
            embed.add_field(name="IMDB Votes", value=imdb_votes, inline=True)
            embed.add_field(name="Rotten", value=rotten_tomatoes, inline=True)
            embed.add_field(name="Rotten Audience", value=rta, inline=True)
            embed.add_field(name="Metacritic", value=metacritic, inline=True)
            embed.add_field(name="Letterboxd", value=lro100, inline=True)
            embed.add_field(name="Metacritic User", value=mu, inline=True)
            embed.add_field(name="Average Score", value=f"{avg:.0f}" if avg != "N/A" else "N/A", inline=True)
            embed.add_field(name="Critic & Director Rank", value=tr, inline=True)
            embed.set_thumbnail(url=data['Poster'])
            await ctx.send(embed=embed)
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    async def t(ctx, *, movie_name):
        try:
            nmn = nt(movie_name)
            url = "http://www.omdbapi.com/?apikey=APIKEY&t=" + nmn.replace(' ', '+')
            async with session.get(url) as r:
                data = await r.json()
            year = None
            if data['Response'] == 'True':
                year = data['Year'].split('–')[0]
            await st(ctx, m=movie_name, y=year, s=session)
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    await bot.start('APIKEY')

if __name__ == "__main__":
    asyncio.run(main())
