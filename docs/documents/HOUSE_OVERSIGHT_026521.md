# HOUSE_OVERSIGHT_026521

## Document Metadata

**Bates Range:** HOUSE_OVERSIGHT_026521 to HOUSE_OVERSIGHT_026542  
**Pages:** 43  
**Custodian:** Epstein, Jeffrey  
**Date Created:** 11/26/2013  
**Original Filename:** CWOL.pdf  
**File Type:** PDF  
**File Size:** 521.7 KB  
**MD5 Hash:** `5baefcad203b4b25db76146138081ebb`

## Entities Mentioned

### People
- [Cambridge University Press](../entities/people/cambridge-university-press.md) - 2 mentions
- [Harvard University](../entities/people/harvard-university.md) - 1 mention
- [San Diego](../entities/people/san-diego.md) - 1 mention
- [John Kerry](../entities/people/john-kerry.md) - 1 mention
- [Computer Science](../entities/people/computer-science.md) - 1 mention
- [Harvard University Press](../entities/people/harvard-university-press.md) - 1 mention
- [John Maynard](../entities/people/john-maynard.md) - 1 mention
- [John Maynard
Keynes](../entities/people/john-maynard-keynes.md) - 1 mention
- [Mr. Obama](../entities/people/mr-obama.md) - 1 mention
- [Evolutionary Dynamics](../entities/people/evolutionary-dynamics.md) - 1 mention

### Organizations
- [CWOL](../entities/organizations/cwol.md) - 32 mentions
- [CWL](../entities/organizations/cwl.md) - 13 mentions
- [Harvard University](../entities/organizations/harvard-university.md) - 2 mentions
- [MIT](../entities/organizations/mit.md) - 2 mentions
- [Cambridge University](../entities/organizations/cambridge-university.md) - 2 mentions
- [Oxford University](../entities/organizations/oxford-university.md) - 1 mention
- [Princeton University](../entities/organizations/princeton-university.md) - 1 mention
- [the Washington Post](../entities/organizations/the-washington-post.md) - 1 mention
- [University Press](../entities/organizations/university-press.md) - 1 mention
- [Cambridge University Press](../entities/organizations/cambridge-university-press.md) - 1 mention

### Locations
- [Cambridge](../entities/locations/cambridge.md) - 2 mentions
- [Washington](../entities/locations/washington.md) - 1 mention
- [Paris](../entities/locations/paris.md) - 1 mention
- [USA](../entities/locations/usa.md) - 1 mention
- [Virginia](../entities/locations/virginia.md) - 1 mention
- [Washington DC](../entities/locations/washington-dc.md) - 1 mention
- [Keynes](../entities/locations/keynes.md) - 1 mention
- [N.Y.](../entities/locations/ny.md) - 1 mention
- [NW](../entities/locations/nw.md) - 1 mention

### Events/Dates
- [2006](../entities/events/2006.md) - 3 mentions
- [1998](../entities/events/1998.md) - 3 mentions
- [2012](../entities/events/2012.md) - 2 mentions
- [2013](../entities/events/2013.md) - 2 mentions
- [2003](../entities/events/2003.md) - 2 mentions
- [1990](../entities/events/1990.md) - 2 mentions
- [1997](../entities/events/1997.md) - 2 mentions
- [1992](../entities/events/1992.md) - 2 mentions
- [1988](../entities/events/1988.md) - 2 mentions
- [1969](../entities/events/1969.md) - 2 mentions

## Document Text

```
﻿Cooperating Without Looking
Moshe Hoffman, 1,2∗† Erez Yoeli, 2,3∗ Martin Nowak 2
1 Department of **Computer Science** and Engineering,
University of California at **San Diego**, La Jolla, CA 92093
2 Program for **Evolutionary Dynamics**,
****Harvard University****, **Cambridge**, MA 02138
2 Federal Trade Commission,
600 Pennsylvania Ave. NW, **Washington**, DC 20004
∗ These authors contributed equally to this work.
† To whom correspondence should be addressed; E-mail: hoffman.moshe@gmail.com.
Cooperation occurs when we take on costs to help others.
A key
mechanism by which cooperation is sustained is reciprocity: individuals
cooperate with those who have cooperated in the past. In
reality, we not only condition on others’ past cooperative actions,
but also on the decision making process that leads to cooperation:
we trust more those who cooperate without calculating the costs
because they will cooperate even when those costs are high.
We
propose a game theory model to explain this phenomenon. In our
model, player 1 chooses whether or not to cooperate with player 2.
Player 1 faces a stochastic temptation to defect and, before choosing
whether to cooperate, also decides whether to “look” at the
realized temptation. Player 2 observes not only whether player 1
ultimately cooperated but also whether she looked, then decides
1
whether or not to continue interacting with player 1. We find conditions
in which there is an equilibrium where player 2 chooses to
interact with player 1 only if player 1 cooperates without looking
(**CWOL**) and player 1 chooses to **CWOL**. We show that this equilibrium
is robust to both high degrees of rationality, as modeled by
subgame perfection and learning or **Evolutionary Dynamics**, as modeled
by the replicator dynamic.
Using computer simulations, we
also show that it emerges with high frequency, even in the presence
of other equilibria. Additionally, we show that the ability for player
1 to avoid looking, and the ability for player 2 to detect looking
increases cooperation. We propose this model as a possible explanation
for a number of interesting phenomena, and thereby derive
novel predictions about these phenomena, including why we dislike
“flip-flopping” politicians and respect principled people more generally,
why people cooperate intuitively, and why people feel disgust
when considering taboo trade-offs, and why people fall in love.
Cooperation occurs when we take on costs to help others. A key mechanism by which
cooperation is sustained is reciprocity: individuals condition their behavior on others’
past actions [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]. In reality, we not only condition
on others’ past actions, but also on the decision-making process that lead to cooperation:
we place more trust in cooperators who do not take time to carefully weigh the costs of
cooperation and who do not try to collect data on such costs before deciding whether to
cooperate. For example, we are impressed by colleagues who agree to proofread a paper
without thinking twice, and view with suspicion those who ask, “how long will it take?”
before agreeing to attend a practice talk. Such considerations are left out of standard
2
models of reciprocity, which only attend to cooperative actions and not the deliberation
process leading up to the action.
We develop a simple model to explain why “looking” at the costs of cooperation is
viewed with suspicion. The explanation we suggest is quite intuitive: those who cooperate
without looking (**CWOL**) can be trusted to cooperate even in times when there are
temptations to defect. While this insight can be captured without the need for a formal
model, it is less clear that cooperators will choose to not look, since they pay a price by
cooperating blindly in tempting circumstances. Moreover, the formal model, as will be
seen, helps explicate when **CWOL** will occur as well as what difference the ability to not
look and to observe others not looking will make.
We formalize this idea using what we call the envelope game (see figure 1).
The
envelope game distills an interaction between two individuals, or players, in an uncertain
environment.
Thus, we start by assuming there is a distribution of payoffs with two
possibilities: one in which defection is relatively tempting, and another in which it is
not. The temptation to defect is randomly determined. Defection is not tempting with
probability p and tempting with probability 1 − p. Both players know how likely it is that
defection is tempting. However, at this point, neither player knows size of the temptation.
That is, the temptation is placed inside an envelope and the envelope is sealed without
the players knowing its content. Next, we assume that one of the players, player 1,
chooses whether to learn the size of the temptation, either via mental deliberation or by
gathering information. We model this in a simplified way by assuming that player 1 has a
dichotomous choice: she can choose to open the envelope and look inside it, or not. If s
```

*[Text truncated to 5000 characters]*

---

## Related Documents

**Similar Documents** (by shared entities):
- [HOUSE_OVERSIGHT_018232](HOUSE_OVERSIGHT_018232.md) - 41 shared entities
- [HOUSE_OVERSIGHT_017526](HOUSE_OVERSIGHT_017526.md) - 36 shared entities
- [HOUSE_OVERSIGHT_020447](HOUSE_OVERSIGHT_020447.md) - 35 shared entities
- [HOUSE_OVERSIGHT_013501](HOUSE_OVERSIGHT_013501.md) - 35 shared entities
- [HOUSE_OVERSIGHT_012899](HOUSE_OVERSIGHT_012899.md) - 35 shared entities
