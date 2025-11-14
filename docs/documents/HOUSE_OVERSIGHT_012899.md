# HOUSE_OVERSIGHT_012899

## Document Metadata

**Bates Range:** HOUSE_OVERSIGHT_012899 to HOUSE_OVERSIGHT_013267  
**Pages:** 737  
**Custodian:** Epstein, Jeffrey  
**Date Created:** 09/19/2013  
**Original Filename:** EngGenInt_Vol_One.pdf  
**File Type:** PDF  
**File Size:** 8.6 MB  
**MD5 Hash:** `029ae4b54f7b9ea4f170f209fcd39e2c`

## Entities Mentioned

### People
- [San Francisco](../entities/people/san-francisco.md) - 1 mention
- [Harvard University](../entities/people/harvard-university.md) - 1 mention
- [Basic Books](../entities/people/basic-books.md) - 1 mention
- [Harvard University Press](../entities/people/harvard-university-press.md) - 1 mention
- [Cambridge University Press](../entities/people/cambridge-university-press.md) - 1 mention
- [Daniel Dennett](../entities/people/daniel-dennett.md) - 1 mention
- [Cognitive Science](../entities/people/cognitive-science.md) - 1 mention
- [Immanuel Kant](../entities/people/immanuel-kant.md) - 1 mention
- [Stephen Wolfram](../entities/people/stephen-wolfram.md) - 1 mention
- [Joscha Bach](../entities/people/joscha-bach.md) - 1 mention

### Organizations
- [Twitter](../entities/organizations/twitter.md) - 1 mention
- [Facebook](../entities/organizations/facebook.md) - 1 mention
- [Google](../entities/organizations/google.md) - 1 mention
- [Fed](../entities/organizations/fed.md) - 1 mention
- [Harvard University](../entities/organizations/harvard-university.md) - 1 mention
- [Microsoft](../entities/organizations/microsoft.md) - 1 mention
- [NASA](../entities/organizations/nasa.md) - 1 mention
- [IBM](../entities/organizations/ibm.md) - 1 mention
- [FCA](../entities/organizations/fca.md) - 1 mention
- [Wikipedia](../entities/organizations/wikipedia.md) - 1 mention

### Locations
- [New York](../entities/locations/new-york.md) - 1 mention
- [America](../entities/locations/america.md) - 1 mention
- [China](../entities/locations/china.md) - 1 mention
- [Germany](../entities/locations/germany.md) - 1 mention
- [Russia](../entities/locations/russia.md) - 1 mention
- [Israel](../entities/locations/israel.md) - 1 mention
- [USA](../entities/locations/usa.md) - 1 mention
- [Boston](../entities/locations/boston.md) - 1 mention
- [Cambridge](../entities/locations/cambridge.md) - 1 mention
- [Hong Kong](../entities/locations/hong-kong.md) - 1 mention

### Events/Dates
- [today](../entities/events/today.md) - 1 mention
- [2008](../entities/events/2008.md) - 1 mention
- [2011](../entities/events/2011.md) - 1 mention
- [2007](../entities/events/2007.md) - 1 mention
- [2010](../entities/events/2010.md) - 1 mention
- [2009](../entities/events/2009.md) - 1 mention
- [2006](../entities/events/2006.md) - 1 mention
- [years](../entities/events/years.md) - 1 mention
- [2012](../entities/events/2012.md) - 1 mention
- [2005](../entities/events/2005.md) - 1 mention

## Document Text

```
﻿Ben Goertzel with Cassio Pennachin & Nil Geisweiller &
the OpenCog Team
Engineering General **Intelligence**, Part 1:
A Path to Advanced AGI via Embodied Learning and
Cognitive Synergy
September 19, 2013

This book is dedicated by Ben Goertzel to his beloved,
departed grandfather, Leo Zwell – an amazingly
warm-hearted, giving human being who was also a deep
thinker and excellent scientist, who got Ben started on the
path of science. As a careful experimentalist, Leo would
have been properly skeptical of the big hypotheses made
here – but he would have been eager to see them put to the
test!

Preface
This is a large, two-part book with an even larger goal: To outline a practical approach to
engineering software systems with general **Intelligence** at the human level and ultimately beyond.
Machines with flexible problem-solving ability, open-ended learning capability, creativity and
eventually, their own kind of genius.
Part 1, this volume, reviews various critical conceptual issues related to the nature of **Intelligence**
and mind. It then sketches the broad outlines of a novel, integrative architecture for
Artificial General **Intelligence** (AGI) called CogPrime ... and describes an approach for giving a
young AGI system (CogPrime or otherwise) appropriate experience, so that it can develop its
own smarts, creativity and wisdom through its own experience. Along the way a formal theory
of general **Intelligence** is sketched, and a broad roadmap leading from here to human-level artificial
**Intelligence**. Hints are also given regarding how to eventually, potentially create machines
advancing beyond human level – including some frankly futuristic speculations about strongly
self-modifying AGI architectures with flexibility far exceeding that of the human brain.
Part 2 then digs far deeper into the details of CogPrime’s multiple structures, processes and
functions, culminating in a general argument as to why we believe CogPrime will be able to
achieve general **Intelligence** at the level of the smartest humans (and potentially greater), and
a detailed discussion of how a CogPrime-powered virtual agent or robot would handle some
simple practical tasks such as social play with blocks in a preschool context. It first describes
the CogPrime software architecture and knowledge representation in detail; then reviews the
cognitive cycle via which CogPrime perceives and acts in the world and reflects on itself; and
next turns to various forms of learning: procedural, declarative (e.g. inference), simulative and
integrative. Methods of enabling natural language functionality in CogPrime are then discussed;
and then the volume concludes with a chapter summarizing the argument that CogPrime can
lead to human-level (and eventually perhaps greater) AGI, and a chapter giving a thought
experiment describing the internal dynamics via which a completed CogPrime system might
solve the problem of obeying the request “Build me something with blocks that I haven’t seen
before.”
The chapters here are written to be read in linear order – and if consumed thus, they tell
a coherent story about how to get from here to advanced AGI. However, the impatient reader
may be forgiven for proceeding a bit nonlinearly. An alternate reading path for the impatient
reader would be to start with the first few chapters of Part 1, then skim the final two chapters of
Part 2, and then return to reading in linear order. The final two chapters of Part 2 give a broad
overview of why we think the CogPrime design will work, in a way that depends on the technical
vii
viii
details of the previous chapters, but (we believe) not so sensitively as to be incomprehensible
without them.
This is admittedly an unusual sort of book, mixing demonstrated conclusions with unproved
conjectures in a complex way, all oriented toward an extraordinarily ambitious goal. Further,
the chapters are somewhat variant in their levels of detail – some very nitty-gritty, some more
high level, with much of the variation due to how much concrete work has been done on the
topic of the chapter at time of writing. However, it is important to understand that the ideas
presented here are not mere armchair speculation – they are currently being used as the basis
for an open-source software project called OpenCog, which is being worked on by software
developers around the world. Right now OpenCog embodies only a percentage of the overall
CogPrime design as described here. But if OpenCog continues to attract sufficient funding
or volunteer interest, then the ideas presented in these volumes will be validated or refuted
via practice. (As a related note: here and there in this book, we will refer to the "current"
CogPrime implementation (in the OpenCog framework); in all cases this refers to OpenCog as
of late 2013.)
To state one believes one knows a workable path to creating a human-level (and potentially
greater) general **Intelligence** is to make a dramatic statement, given the conventional way of
thinking about the t
```

*[Text truncated to 5000 characters]*

---

## Related Documents

**Similar Documents** (by shared entities):
- [HOUSE_OVERSIGHT_018232](HOUSE_OVERSIGHT_018232.md) - 124 shared entities
- [HOUSE_OVERSIGHT_015675](HOUSE_OVERSIGHT_015675.md) - 104 shared entities
- [HOUSE_OVERSIGHT_017526](HOUSE_OVERSIGHT_017526.md) - 100 shared entities
- [HOUSE_OVERSIGHT_016804](HOUSE_OVERSIGHT_016804.md) - 97 shared entities
- [HOUSE_OVERSIGHT_016221](HOUSE_OVERSIGHT_016221.md) - 97 shared entities
