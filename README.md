<p align="center">
  <a href="https://github.com/ananyapuru/381-final-project/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/ananyapuru/381-final-project?style=for-the-badge" alt="Contributors">
  </a>
  <a href="https://github.com/ananyapuru/381-final-project/network/members">
    <img src="https://img.shields.io/github/forks/ananyapuru/381-final-project?style=for-the-badge" alt="Forks">
  </a>
  <a href="https://github.com/ananyapuru/381-final-project/stargazers">
    <img src="https://img.shields.io/github/stars/ananyapuru/381-final-project?style=for-the-badge" alt="Stargazers">
  </a>
  <a href="https://github.com/ananyapuru/381-final-project/issues">
    <img src="https://img.shields.io/github/issues/ananyapuru/381-final-project?style=for-the-badge" alt="Issues">
  </a>
  <a href="https://github.com/ananyapuru/381-final-project/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/ananyapuru/381-final-project?style=for-the-badge" alt="License">
  </a>
  <a href="https://linkedin.com/in/ananya-purushottam">
    <img src="https://img.shields.io/badge/LinkedIn-blue?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
</p>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ananyapuru/381-final-project/">
    <img src="https://cdn-icons-png.flaticon.com/512/8637/8637099.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">A Knowledge Distillation Driven Model for Efficient Cross-Region Housing Price Prediction</h3>

  <p align="center">
    This project aims to develop a machine learning model(s) that accurately predicts house sale prices based on a variety of features regarding the property (such as lot area and interior/exterior design), its surrounding area, and its sale information.
    <br />
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

### Introduction

#### Overview
This project aims to develop a machine learning model that accurately predicts house sale prices based on a variety of features regarding the property (such as lot area and interior/exterior design), its surrounding area, and its sale information.

We are interested in investigating if variations in housing prices follow the same trend/factors across different geographical locations. Specifically, we will determine whether a model trained on general features across multiple different geographic regions or a model trained on region-specific features is more effective in making housing price predictions. Further, the project seeks to examine if predictors identified as important across various regions are equally effective for a specific region (London) through knowledge distillation [1].

#### Motivation
In general, being able to accurately estimate housing prices plays a crucial role in the real estate industry and has many implications a variety of stakeholders, such as real estate professionals, home buyers, and home sellers. Precise price predictions can help buyers understand the fair market value of different properties and help current homeowners make better-informed selling decisions, helping them avoid overpaying and learn how to negotiate more effectively. For real estate agents, reliable and accurate pricing models provide more informed market analysis, better client advising, and improved investment decisions. This will make the housing market more transparent overall.

#### General Approach
Our approach was guided by discussions with Professor Wong and involves two complementary analyses:

1. **Teacher-Student Knowledge Distillation:**
First, a "teacher" model will be trained on a combined dataset consisting of multiple regions (California, Paris, Perth, London, New York) to capture generalizable predictive insights. Then, we will train a "student" model specifically on the London housing data using an output-level knowledge distillation method, whereby the student model learns from the teacher model's predictions on the London dataset, alongside the London dataset's ground truth labels. This will follow the suggested joint loss model as recommeded by Professor Wong. We will then compare the distilled student model's performance to a baseline model trained solely on the London dataset to assess performance.

2. **Feature Importance Analysis:**
We will identify and compare top predictors separately from the teacher model (trained on combined datasets and potentially each city's datasets individually) and the student model (trained on London). By comparing these predictors, we will assess whether general features identified across multiple regions also serve as important predictors specifically for London or if location-specific factors tend to dominate. This may also allow us to determine if the type of feature, such as property interior/exterior design versus its surrounding area, impact the feature's importance.

The use of knowledge distillation allows us to train a simpler model for regression on the London dataset for better efficiency. Although we anticipate that there is no significant need for us to be concerned with efficiency for the datasets we are handling, we believe this attempt will still be fruitful nonetheless as knowledge distillation is an interesting, cutting-edge technique that is useful to pick up.


### Built With

[![Python][Python-badge]][Python-url]

[![Pandas][Pandas-badge]][Pandas-url]

[![Jupyter][Jupyter-badge]][Jupyter-url]

[![GitHub][GitHub-badge]][GitHub-url]


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites
This project assumes the user has already downloaded `[Python]([url](https://www.python.org/downloads/))` and the `[Pip](https://pip.pypa.io/en/stable/installation/)` package-management system.

**To Run Sanitization Script `sanitize.py`**
1. Set up a virtual environment [Optional]
2. Change directory into `Sanitization`
3. Run `pip install -r requirements.txt` to download all required packages
4. Run `python3 sanitize.py` to execute the script.


### Installation & Usage 

1. From the root, run `python3 Sanitization/sanitize.py` to execute the sanitization script and generate `combined_dataset.csv` [Optional since the CSV already exists]
2. Similarly, run the feature engineering scripts found in the `feature-engineering` directory to create `final_enriched_dataset.csv` [Optional since the CSV already exists in the repository]
3. Lastly, run the Jupyter notebook `model/model.ipynb` to generate the teacher-student and baseline models and compute metrics and plots to assess accuracy.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the [MIT License](https://opensource.org/license/mit)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact
- Ananya Purushottam -- ananya.purushottam@yale.edu
- Helen Zhou -- helen.zhou@yale.edu
- Ian Lim -- ian.lim@yale.edu
- Nevin Tan - nevin.tan@yale.edu

Project Link: [https://github.com/ananyapuru/381-final-project](https://github.com/ananyapuru/381-final-project)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* We'd like to acknowledge Professor Wong and the CPSC 381 Teaching Staff for their guidance and feedback throughout the semester.
* We'd also like to acknowledge Kaggle for supplying all the different housing datasets used.
* We'd also like to acknowledge the source of this README template. This README template can be found [here](https://github.com/othneildrew/Best-README-Template/tree/main).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/ananyapuru/381-final-project.svg?style=for-the-badge
[contributors-url]: https://github.com/ananyapuru/381-final-project/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ananyapuru/381-final-project.svg?style=for-the-badge
[forks-url]: https://github.com/ananyapuru/381-final-project/network/members
[stars-shield]: https://img.shields.io/github/stars/ananyapuru/381-final-project.svg?style=for-the-badge
[stars-url]: https://github.com/ananyapuru/381-final-project/stargazers
[issues-shield]: https://img.shields.io/github/issues/ananyapuru/381-final-project.svg?style=for-the-badge
[issues-url]: https://github.com/ananyapuru/381-final-project/issues
[license-shield]: https://img.shields.io/github/license/ananyapuru/381-final-project.svg?style=for-the-badge
[license-url]: https://opensource.org/license/mit
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/ananya-purushottam
[product-screenshot]: images/screenshot.png
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Pandas-badge]: https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white
[Pandas-url]: https://pandas.pydata.org/
[Jupyter-badge]: https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white
[Jupyter-url]: https://jupyter.org/
[GitHub-badge]: https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white
[GitHub-url]: https://github.com/
