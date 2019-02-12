# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from typing import Dict, List, TYPE_CHECKING, Type

# -- third party --
# -- own --
from game.autoenv import Game
from game.base import AbstractPlayer, EventDispatcher, EventHandler
from thb.cards.base import CardList, Deck
from thb.characters.base import Character
from utils.misc import BatchList

# -- typing --
if TYPE_CHECKING:
    from thb.common import PlayerIdentity  # noqa: F401


# -- code --
class THBEventDispatcher(EventDispatcher):
    game: 'THBattle'

    def populate_handlers(self) -> List[EventHandler]:
        from thb.actions import COMMON_EVENT_HANDLERS
        g = self.game
        ehclasses = list(COMMON_EVENT_HANDLERS) + list(g.game_ehs)
        for c in g.players:
            ehclasses.extend(c.eventhandlers)

        return EventHandler.make_list(g, ehclasses)


class THBattle(Game):
    game: 'THBattle'
    game_ehs: List[Type[EventHandler]]
    deck: Deck
    players: BatchList[Character]
    id: Dict[AbstractPlayer, 'PlayerIdentity']

    dispatcher_cls = THBEventDispatcher