# unitaryDESIGN

Contribute to the open source ecosystem, level your skills, and get rewarded!

[unitaryDESIGN](https://unitary.design/) is a virtual event encouraging people to make contributions to the open source quantum ecosystem through the lens of community engagement and science communication.
The event will run February 16&mdash;27, 2026, and hackers have the opportunity to win cash bounties!
This is our inaugural run of unitaryDESIGN, and we're excited to have you join us!

Read our hacker guide for more info and join our [Discord](https://discord.gg/a3EnYsT2rQ) if you have questions.
And if you're curious how things will be formatted, take a look at Unitary Foundation's other annual hackathon, [unitaryHACK](https://unitaryhack.dev/).

We're looking forward to working with you. Make sure you register to be eligible to claim your bounties!

---

## 🚀 Website development

Want to help improve the unitaryDESIGN website?
The website is built with [11ty](https://www.11ty.dev/) and hosted on GitHub Pages.
The [Fernfolio](https://fernfolio.netlify.app/) template was used to bootstrap the design.
Here are some basic local setup steps to get you started:

### Local environment

- Clone the repo
- Navigate to the directory `cd untitar.design`
- Install the goods `npm install`
- Run it `npm start`
- You should now be able to see everything running on http://localhost:8080
- Make your changes and open a pull request on github


## 🌐 Deployment

- Pushes to `main` run `.github/workflows/buildsite.yaml`, build with Node, and deploy to GitHub Pages using `PATH_PREFIX=/`, `INCLUDE_CNAME=true`, and `SITE_URL=https://unitary.design/` (so `src/CNAME` is published for the production domain).
- Manual runs expose a `target` input; choose `github-pages` to rebuild with `PATH_PREFIX=/uhack-test/`, skip the `CNAME`, and stamp links with `SITE_URL=https://unitaryfoundation.github.io/uhack-test` for testing on a repo-scoped Pages URL.
- Locally you can mirror those targets: `npm run clean && npm run build` for production, or `npm run clean && PATH_PREFIX=/uhack-test/ INCLUDE_CNAME=false SITE_URL=https://unitaryfoundation.github.io/uhack-test npm run build` for the GitHub Pages preview.
- Asset URLs already honor `PATH_PREFIX`, and when you open `_site/index.html` directly the build rewrites links for `file://`, though serving `_site` via `npm start` (or any static server) gives the most accurate preview.
