# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import ActionStageLaunchCard, Damage, DrawCardStage, GenericAction
from gamepack.thb.actions import PlayerTurn, ttags
from gamepack.thb.cards import AttackCard, AttackCardHandler, BaseAttack, BaseDuel, DuelCard
from gamepack.thb.cards import ElementalReactorSkill, Skill, UserAction, t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class CriticalStrike(Skill):
    associated_action = None
    skill_category = ('character', 'active')
    target = t_None


class CriticalStrikeAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        ttags(tgt)['flan_cs'] = True
        tgt.tags['flan_targets'] = []
        return True


class CriticalStrikeHandler(EventHandler):
    execute_after = (
        'AttackCardHandler',
        'FrozenFrogHandler',
        'ElementalReactorHandler',
        'ReversedScalesHandler',
    )
    execute_before = (
        'MomijiShieldHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if not tgt.has_skill(CriticalStrike): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(CriticalStrikeAction(tgt, tgt))

            act.amount = max(0, act.amount - 1)

        elif evt_type == 'action_apply' and isinstance(act, BaseAttack):
            src = act.source
            tags = src.tags
            if not self.in_critical_strike(src):
                return act

            tgt = act.target
            if isinstance(act, BaseAttack):
                tags['flan_targets'].append(tgt)
                act.damage += 1

        elif evt_type == 'action_before' and isinstance(act, Damage):
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, BaseDuel):
                return act

            src, tgt = act.source, act.target

            if not self.in_critical_strike(src):
                return act

            act.amount += 1

        elif evt_type == 'action_can_fire':
            arg = act
            act, valid = arg
            if not isinstance(act, ActionStageLaunchCard): return arg
            c = act.card
            src = act.source
            tags = src.tags
            if not self.in_critical_strike(src): return arg
            if not c.is_card(AttackCard): return arg
            if src.has_skill(ElementalReactorSkill): return arg
            if set(act.target_list) & set(tags['flan_targets']):
                return (act, False)

            return arg

        elif evt_type == 'action_stage_action':
            tgt = act
            if not self.in_critical_strike(tgt): return act
            AttackCardHandler.set_freeattack(tgt)

        return act

    def in_critical_strike(self, p):
        return (
            ttags(p)['flan_cs'] and
            Game.getgame().current_turn is p and
            p.has_skill(CriticalStrike)
        )


class Exterminate(Skill):
    associated_action = None
    skill_category = ('character', 'active')
    target = t_None


class ExterminateAction(UserAction):

    def apply_action(self):
        src, tgt = self.source, self.target
        tgt.tags['exterminate'] = src
        return True


class ExterminateHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            act, tl = arg
            src = act.source
            g = Game.getgame()

            if not src.has_skill(Exterminate):
                return arg

            c = act.card
            if not c.is_card(AttackCard) and not c.is_card(DuelCard):
                return arg

            for p in g.players:
                p.has_skill.hook(self.has_skill_hook)

            for tgt in tl:
                g.process_action(ExterminateAction(src, tgt))

        elif evt_type == 'action_after' and isinstance(arg, PlayerTurn):
            g = Game.getgame()
            for p in g.players:
                p.tags.pop('exterminate', '')

        return arg

    def has_skill_hook(self, callnext, marker, tgt, skill):
        g = Game.getgame()
        if self not in g.event_handlers:
            # clean up
            for p in g.players:
                p.tags.pop('exterminate', '')
                p.has_skill.unhook(self.has_skill_hook)

            return callnext(marker, tgt, skill)

        src = tgt.tags['exterminate']
        if src and src.has_skill(Exterminate):
            if 'character' in skill.skill_category:
                return False

        return callnext(marker, tgt, skill)


@register_character
class Flandre(Character):
    skills = [CriticalStrike, Exterminate]
    eventhandlers_required = [CriticalStrikeHandler, ExterminateHandler]
    maxlife = 4
