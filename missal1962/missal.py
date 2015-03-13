"""
Missal 1962
"""

from datetime import date, timedelta
from dateutil.easter import easter
from missal1962.rules import ruleset
import sys
import constants


class Missal(list):
    """ Class representing a missal.

    It's a list of lists, each one representing one day as following
    structure:
      [<date object>, [<list of day identifiers]]
      for example:
      ...
      [datetime.date(2008, 5, 3), ['sab_post_ascension',
                                   '05-03.mariae_reginae_poloniae']]
      [datetime.date(2008, 5, 4), ['dom_post_ascension', '05-04']]
      [datetime.date(2008, 5, 5), ['f2_hebd_post_ascension', '05-05']]
      [datetime.date(2008, 5, 6), ['f3_hebd_post_ascension']]
      ...
    """
    def __init__(self, year):
        """ Build an empty missal and fill it in with liturgical days'
        identifiers.
        """
        # build empty missal
        day = date(year, 1, 1)
        while day.year == year:
            self.append([day, []])
            day += timedelta(days=1)

        # fill in variable days
        # main blocks
        self._insert_block(
            self._calc_varday__dom_sanctae_familiae(year),
            constants.vardays__post_epiphania)
        self._insert_block(
            self._calc_varday__dom_septuagesima(year),
            constants.vardays__ressurectionis)
        self._insert_block(
            self._calc_varday__sab_before_dom_post_pentecost_24(year),
            constants.vardays__post_epiphania,
            reverse=True,
            overwrite=False)
        self._insert_block(
            self._calc_varday__dom_post_pentecost_24(year),
            constants.vardays__hebd_post_pentecost_24)
        self._insert_block(
            self._calc_varday__dom_adventus(year),
            constants.vardays__advent,
            stop_date=date(year, 12, 23))
        # additional blocks
        self._insert_block(
            self._calc_varday__sanctissimi_nominis_jesu(year),
            constants.vardays__sanctissimi_nominis_jesu
        )
        self._insert_block(
            self._calc_varday__quattour_septembris(year),
            constants.vardays__quattour_septembris)
        self._insert_block(
            self._calc_varday__jesu_christi_regis(year),
            constants.vardays__jesu_christi_regis
        )
        if self._calc_varday__dom_octavam_nativitatis(year):
            self._insert_block(
                self._calc_varday__dom_octavam_nativitatis(year),
                constants.vardays__dom_octavam_nativitatis
            )

        # fill in fixed days
        for date_, contents in self:
            date_id = date_.strftime("%m_%d")
            days = list(set([ii for ii in constants.fixdays
                             if ii.startswith(date_id)]))
            contents.extend(days)

        # at this point missal is prepopulated with days' IDs
        # now apply rules to resolve the conflicts when
        # more than two days appeared on the same date
        for date_, contents in self:
            if len(contents) > 2:
                # if more than 2 ids, cut the lowest class
                # ['03_08_1:3', 'sab_quadragesima_4:2', '03_08_2:4']
                #                 vvvv
                # ['sab_quadragesima_4:2', '03_08_1:3']
                contents.remove(
                    sorted(contents, key=lambda x: x.split(':')[1])[-1])

    def get_day_by_id(self, dayid):
        """ Return a list representing single day.

        :param dayid: liturgical days'identifier, for example
                      'f2_sexagesima'
        :type dayid: string
        :return: liturgical day
        :rtype: list(datetime, list)
        """
        for day in self:
            if dayid in day[1]:
                return day

    def _insert_block(self, start_date, block, stop_date=None, reverse=False,
                      overwrite=True):
        """ Insert a block of related liturgical days'identifiers.

        :param start_date: date where first or last (if `reverse`=True)
                           element of the block will be inserted
        :type start_date: date object
        :param block: list of identifiers in established order
        :type block: list of strings
        :param stop_date: last date to insert block element
        :type stop_date: date object
        :param reverse: if False, identifiers will be put in days
                        following `start_date` otherwise they'll
                        be put in leading up days
        :param overwrite: if True, overwrite existing identifiers,
                          else quit on first non empty day

        Example:
        start_date=2008-01-13, reverse=False
        block = [
            'dom_sanctae_familiae',
            'f2_post_epiphania_1',
            'f3_post_epiphania_1',
        ]
        Result:
        ...
        [datetime.date(2008, 1, 13), ['dom_sanctae_familiae']]
        [datetime.date(2008, 1, 14), ['f2_post_epiphania_1', '01-14']]
        [datetime.date(2008, 1, 15), ['f3_post_epiphania_1', '01-15']]
        ...

        Example:
        start_date=2008-11-22, reverse=True
        block = [
            'f5_post_epiphania_6',
            'f6_post_epiphania_6',
            'sab_post_epiphania_6'
        ]
        Result:
        ...
        [datetime.date(2008, 11, 20), ['f5_post_epiphania_6']]
        [datetime.date(2008, 11, 21), ['f6_post_epiphania_6']]
        [datetime.date(2008, 11, 22), ['sab_post_epiphania_6']]
        ...
        """
        if reverse:
            block = reversed(block)
        day_index = self._get_date_index(start_date)
        for ii, day in enumerate(block):
            index = day_index + ii if not reverse else day_index - ii
            # skip on empty day in a block
            if not day:
                continue
            # break on first non-empty day
            if self[index][1] and not overwrite:
                break
            # break on stop date
            if stop_date == self[index - 1][0]:
                break
            self[index][1] = [day]

    def _get_date_index(self, date_):
        """ Return list index where `date_` is located.

        :param date_: date to look up
        :type date_: date object
        :return: index of the list
        :rtype: integer
        """
        for ii, day in enumerate(self):
            if day[0] == date_:
                return ii

    def _calc_varday__dom_ressurectionis(self, year):
        """ Dominica Ressurectionis - Easter Sunday """
        return easter(year)

    def _calc_varday__dom_sanctae_familiae(self, year):
        """ Dominica Sanctae Familiae Jesu Mariae Joseph

        First Sunday after Epiphany (06 January)
        """
        d = date(year, 1, 6)
        wd = d.weekday()
        delta = 6 - wd if wd < 6 else 7
        return d + timedelta(days=delta)

    def _calc_varday__dom_septuagesima(self, year):
        """ Dominica in Septuagesima

        Beginning of the pre-Lenten season
        First day of the Ressurection Sunday - related block.
        It's 63 days before Ressurection.
        """
        return self._calc_varday__dom_ressurectionis(year) - timedelta(days=63)

    def _calc_varday__dom_adventus(self, year):
        """ Dominica I Adventus

        First Sunday of Advent - November 27 if it's Sunday
        or closest Sunday
        """
        d = date(year, 11, 27)
        wd = d.weekday()
        if wd != 6:
            d += timedelta(days=6 - wd)
        return d

    def _calc_varday__dom_post_pentecost_24(self, year):
        """ Dominica XXIV Post Pentecosten

        Last Sunday before Dominica I Adventus
        This will be always dom_post_pentecost_24, which will be
        placed either
        * instead of dom_post_pentecost_23 - if number of
          dom_post_pentecost_* == 23)
        * directly after week of dom_post_pentecost_23 - if number of
          dom_post_pentecost_* == 24)
        * directly after week of dom_post_epiphania_6 (moved from post
          epiphania period) - if number of dom_post_pentecost_* > 24)
        """
        return self._calc_varday__dom_adventus(year) - timedelta(days=7)

    def _calc_varday__sab_before_dom_post_pentecost_24(self, year):
        """ Last Saturday before Dominica XXIV Post Pentecosten

        This is the end of potentially "empty" period that might appear
        between Dominica XXIII and Dominica XXIV Post Pentecosten if
        Easter is early. In such case Dominica post Epiphania * are
        moved here to "fill the gap"
        """
        return self._calc_varday__dom_post_pentecost_24(year) - timedelta(days=1)

    def _calc_varday__quattour_septembris(self, year):
        """ Feria Quarta Quattuor Temporum Septembris

        Ember Wednesday in September is Wednesday after third Sunday
        of September according to John XXIII's motu proprio
        Rubricarum instructum of June 25 1960.
        """
        d = date(year, 9, 1)
        while d.month == 9:
            # third Sunday
            if d.weekday() == 6 and 15 <= d.day <= 21:
                break
            d += timedelta(days=1)
        # Wednesday after third Sunday
        return d + timedelta(days=3)

    def _calc_varday__sanctissimi_nominis_jesu(self, year):
        """ Sanctissimi Nominis Jesu

        The Feast of the Holy Name of Jesus. Kept on the First
        Sunday of the year; but if this Sunday falls on
        1st, 6th or 7th January, the feast is kept on 2nd January.
        """
        d = date(year, 1, 1)
        while d.day <= 7:
            wd = d.weekday()
            if d.day in (1, 6, 7) and wd == 6:
                return date(year, 1, 2)
            if wd == 6:
                return d
            d += timedelta(days=1)

    def _calc_varday__jesu_christi_regis(self, year):
        """ Jesu Christi Regis

        The Feast of Christ the King, last Sunday of October
        """
        d = date(year, 10, 31)
        while d.month == 10:
            if d.weekday() == 6:
                return d
            d -= timedelta(days=1)

    def _calc_varday__dom_octavam_nativitatis(self, year):
        """ Dominica infra octavam Nativitatis

        Sunday within the Octave of Christmas, Sunday between
        Dec 26 and Dec 31
        """
        d = date(year, 12, 27)
        while d.year == year:
            if d.weekday() == 6:
                return d
            d += timedelta(days=1)
        return None

if __name__ == '__main__':
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2008
    missal = Missal(year)

    for ii in missal:
            print ii[0].strftime('%A'), len(ii)
