# RetroStories - E-Ink Monochrome Archive

A beautiful, simple, and distraction-free stories application. Designed with a clean, high-contrast e-ink aesthetic that is extremely gentle on the eyes. It features stories from **Osho**, **Zen masters**, **Sadhguru**, **Aesop's Fables**, and **Jiddu Krishnamurti (JK)**.

Because stories are loaded as Javascript data variables, **you can run this app locally by simply double-clicking `index.html`**—no local web server or CORS configurations required!

---

## 🚀 How to Host this Website on GitHub Pages (Free & Easy)

To put this website online for free using GitHub Pages:

1. **Create a GitHub Account:** If you don't have one, sign up at [github.com](https://github.com).
2. **Create a New Repository:**
   - Click the **New** button in GitHub (or go to [github.com/new](https://github.com/new)).
   - Name your repository (for example: `retro-stories`).
   - Keep it **Public** and do not add a README (we already have one!). Click **Create repository**.
3. **Upload Your Files:**
   - On the quick setup page, click the **"uploading an existing file"** link.
   - Drag and drop **all files and folders** from your local directory (`index.html`, `style.css`, `app.js`, `stories-index.js`, and the entire `stories/` folder) into the box.
   - Click **Commit changes** at the bottom of the page.
4. **Enable GitHub Pages:**
   - In your repository, click the **Settings** tab at the top right.
   - In the left sidebar, click **Pages**.
   - Under the **Build and deployment** section:
     - Set Source to **Deploy from a branch**.
     - Under Branch, click the dropdown, select **`main`** (or `master`), leave folder as `/ (root)`, and click **Save**.
5. **Get Your URL:**
   - Within 1–2 minutes, refresh the Pages settings page. You will see a banner at the top saying: *"Your site is live at `https://<your-username>.github.io/retro-stories/`"*.
   - Click the link to view your live site!

---

## ✍️ How to Add a New Story Yourself (No Coding Required)

Stories are saved by author inside their respective files inside the `stories/` folder (e.g. `stories/osho.js`, `stories/zen.js`, `stories/jk.js`, `stories/sadhguru.js`, `stories/aesop.js`). 

To add a new story directly on GitHub using your web browser:

1. Go to your repository on GitHub.
2. Click on the `stories` folder, then click on the file for the author of your story (e.g. `stories/osho.js`).
3. Click the pencil icon ✏️ at the top right to **Edit this file**.
4. Scroll down to the end of the array and paste your new story block. Ensure it is separated from the previous block by a comma. For example:
   ```javascript
   {
     id: "the-monkey-mind",
     title: "The Monkey Mind",
     author: "Sadhguru",
     category: "Wisdom",
     content: `A disciple went to a guru and asked for a mantra...`
   }
   ```
5. Scroll down and click **Commit changes**.

**That's it!** The website will automatically fetch the new story. It works locally on your machine immediately and updates on GitHub Pages in about 30 seconds.

---

## 📬 How Story Submissions Work

When a reader fills out the **Submit Story** form on your site, they have two options:

### Option A: Submit on GitHub (Recommended)
1. The user clicks **`[ SUBMIT ON GITHUB ]`**.
2. They are redirected to your repository's "New Issue" page on GitHub, with the title, categories, story content, and config block **already pre-filled**!
3. They click **Submit new issue**.
4. You will get a notification on GitHub. To accept it, edit the corresponding author's JS file (e.g. `stories/sadhguru.js`) in your browser, copy-paste the pre-formatted JS block from the issue, and commit!

### Option B: Submit via Email
1. The user clicks **`[ SUBMIT VIA EMAIL ]`**.
2. The site copies the formatted story block to their clipboard and opens their email client pre-addressed to your email.
3. They send the email. When you receive it, simply copy-paste the block into the author's file on GitHub.
