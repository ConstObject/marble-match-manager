import logging
import json
from typing import Union
from datetime import datetime, timedelta

logger = logging.getLogger(f'marble_match.{__name__}')


def update_last_used(index: int):

    x = {
        "id": index,
        "last_used": datetime.utcnow()
    }

    with open('friendlies.json', 'r+') as friendlies:

        written = False

        # Load existing data into a dict
        file_data = json.load(friendlies)

        for i in file_data['users']:
            if i['id'] == index:
                file_data['users'][file_data['users'].index(i)] = x
                written = True

        if not written:
            file_data['users'].append(x)

        # Set files current position at offset
        friendlies.seek(0)
        # Convert back to json

        json.dump(file_data, friendlies, indent=4, sort_keys=True, default=str)


def read_last_used(index: int) -> Union[datetime, int]:
    x = None
    date = 0

    with open('friendlies.json', 'r+') as friendlies:
        x = json.load(friendlies)
        for fields in x['users']:
            if fields['id'] == index:
                date = datetime.strptime(fields['last_used'], '%Y-%m-%d %H:%M:%S.%f')

    return date
