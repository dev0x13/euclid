# Euclid: Universal Experiment Research Results Storage

This repository hosts a source code for an attempt of creating a universal experiment research results storage. The system is intended to solve the following issues of data storage organiztion in small scientific workgroups:

1. **Locality**. Data is stored locally, without any external access. E.g. experiment results are stored on the HDD of one researcher, when others work remotely. Because of that, data transfer may be only performed via a personal meeting or via sending data in an untrasparent fasion.
2. **Lack of structure**. It is common not to have a standard format to store experiment metadata even in a small scientific workgroup. Due to that, it is impossible to reproduce the experiment and to correctly interpret its results. Moreover, this approach makes new researcher onboarding more difficult .
3. **Loss of relevance**. Data loses its relevance, because of the two points above: there is no way to receive the latest data with a minor delay.

This project was a part of a university course, so the detailed system description with UML diagrams and case study can be found at the following document (it is in Russian).
