import asyncio
import aiohttp, ujson as json
from async_lru import alru_cache
from enum import Enum
import private
        
class region(Enum):
    na1 = "1"
    euw1 = "2"
    kr = "3"
    eun1 = "4"
    br1 = "5"
    las = "6"
    la2 = "7"
    oc1 = "8"
    ru = "9"
    tr1 = "10"
    jp1 = "11"
    world = "12"
    
class tiers(Enum):
    challenger = "1"
    master = "2"
    diamond = "3"
    platinum = "4"
    gold = "5"
    silver = "6"
    bronze = "7"
    overall = "8"
    platinum_plus = "10"
    diamond_plus = "11"
    diamond_2_plus = "12"
    grandmaster = "13"
    master_plus = "14"
    iron = "15"
    
class positions(Enum):
    jungle = "1"
    support = "2"
    adc = "3"
    top = "4"
    mid = "5"
    none = "6"
    
class data(Enum):
    perks = 0
    summoner_spells = 1
    start_items = 2
    mythic_and_core = 3
    abilities = 4
    other_items = 5
    shards = 8

class __stats__():
    def __init__(self):
        self
    
    @alru_cache(maxsize=1)
    async def stats(name):
        statsVersion = '1.1'
        overviewVersion = '1.5.0'
        baseOverviewUrl = 'https://stats2.u.gg/lol'
        gameMode = "ranked_solo_5x5"
        ddragon_version = (await private.ddragondata())
        lolVersion = ddragon_version.split(".")
        champName = await private.champnamecleaner(name=name)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/en_US/champion.json") as champJson:
                championId = json.loads(await champJson.text())["data"][f"{champName}"]["key"]
        uggLoLVersion = lolVersion[0] + '_' + lolVersion[1]
    
        async with aiohttp.ClientSession() as session2:
            async with session2.get(f"{baseOverviewUrl}/{statsVersion}/overview/{uggLoLVersion}/{gameMode}/{championId}/{overviewVersion}.json") as URL:
                print(f"{baseOverviewUrl}/{statsVersion}/overview/{uggLoLVersion}/{gameMode}/{championId}/{overviewVersion}.json")
                page = json.loads(await URL.text())
        return page
    
    @alru_cache(maxsize=1)
    async def value_extract(name: str, role='', rank='platinum_plus', region='world'):
        champ = await private.champnamecleaner(name=name)
        lane = "?rank=" + rank.lower() + "&region=" + region.lower() + '&role=' + role.lower()
        url = f"https://u.gg/lol/champions/{champ}/build{lane}"
        soup = await private.beautifulsoup(url=url)
        stats_array = soup.find_all('div', class_='value')
        return stats_array
    
class ugg():
    def __init__(self):
        self
    #Data is gotten in the order 'Tier, Win rate, Rank, Pick rate, ban rate, matches' when using find all
    #We use scraping because this data does not exist in U.GGs JSON files
    #The underlying array is cached, so well the initial scrape takes a bit, the following uses are quite quick
    async def tiers(name, role='', rank='platinum_plus', region='world'):
        tier  = await __stats__.value_extract(name, role, rank, region)
        return tier[0].text
    
    async def winrate(name, role='', rank='platinum_plus', region='world'):
        wr  = await __stats__.value_extract(name, role, rank, region)
        return wr[1].text
    
    async def rank(name, role='', rank='platinum_plus', region='world'):
        rank  = await __stats__.value_extract(name, role, rank, region)
        return rank[2].text
    
    async def totalmatches(name, role='', rank='platinum_plus', region='world'):
        pr = await __stats__.value_extract(name, role, rank, region)
        return pr[5].text   
    
    async def pickrate(name, role='', rank='platinum_plus', region='world'):
        pr = await __stats__.value_extract(name, role, rank, region)
        return pr[3].text
    
    async def banrate(name, role='', rank='platinum_plus', region='world'): 
        br = await __stats__.value_extract(name, role, rank, region)
        return br[4].text
    
    @alru_cache(maxsize=1)
    async def runes(name, role, ranks='platinum_plus', regions='world'):
        ddragon_version = (await __stats__.ddragon_data())
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/en_US/runesReforged.json") as dd_runes:
                runes_json = json.loads(await dd_runes.text())
  
        trees = (await __stats__.stats(name=name))[region[regions.lower()].value][tiers[ranks.lower()].value][positions[role.lower()].value][0][data.perks.value]
        rune_ids = trees[4]
        runes_1 = []
        runes_2 = []
        
        for tree in runes_json: 
            if tree['id'] == trees[2]:
                [runes_1.insert(slots_pos, rune_data['name']) for slots_pos, slots in enumerate(tree["slots"]) for rune_data in slots['runes'] for y in range(6) if rune_ids[y] == rune_data['id']]
            elif tree['id'] == trees[3]:
                [runes_2.insert(slots_pos - 1, rune_data['name']) for slots_pos, slots in enumerate(tree["slots"]) for rune_data in slots['runes'] for y in range(6) if rune_ids[y] == rune_data['id']]

        runes = runes_1 + runes_2
        return runes
    
    @alru_cache(maxsize=1)
    async def items(name, role, ranks='platinum_plus', regions='world'):
        ddragon_version = (await __stats__.ddragon_data())
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/en_US/item.json") as dd_items:
                items_json = json.loads(await dd_items.text())
        
        items = (await __stats__.stats(name=name))[region[regions.lower()].value][tiers[ranks.lower()].value][positions[role.lower()].value][0]
        start = []
        core = []
        last_set = set()
        
        print(items[2])
        for z in items_json['data']:\
            #These can be empty. This is the fault of U.GG, not me.
            [start.append(items_json['data'][z]['name']) for i in items[data.start_items.value][2] if str(i) == z]
            [core.append(items_json['data'][z]['name']) for i in items[data.mythic_and_core.value][2] if str(i) == z]
            {last_set.add(items_json['data'][z]['name']) for x in range(3) for y in range(len(items[data.other_items.value][x])) if str(items[data.other_items.value][x][y][0]) == z}
            
        Items = [start, core, list(last_set)]
        return Items
        
    @alru_cache(maxsize=1)
    async def shards(name, role, ranks='platinum_plus', regions='world'):
        stat_shard_id = (await __stats__.stats(name=name))[region[regions.lower()].value][tiers[ranks.lower()].value][positions[role.lower()].value][0][data.shards.value][2]
        stat_shard = []
        for s in stat_shard_id:
            match s:
                case "5001": stat_shard.append("Health")
                case "5008": stat_shard.append("Adaptive Force")
                case "5007": stat_shard.append("Ability Haste")
                case "5002": stat_shard.append("Armor")
                case "5005": stat_shard.append("Attack Speed")
                case "5003": stat_shard.append("Magic Resist")
        return stat_shard
    
    @alru_cache(maxsize=5)
    async def abilities(name, role, ranks='platinum_plus', regions='world'):
        abilities = (await __stats__.stats(name=name))[region[regions.lower()].value][tiers[ranks.lower()].value][positions[role.lower()].value][0][data.abilities.value][2]
        return abilities