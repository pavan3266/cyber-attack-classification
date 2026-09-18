# Put the project on GitHub

1. Create your account at https://github.com/signup using your own email. Keep credentials private.
2. Sign in, select the plus menu and **New repository**.
3. Suggested name: `cyber-attack-classification`.
4. Suggested description: `Post-publication ML classification companion: reproducible Python experiments, synthetic demo, and CSV benchmark support.`
5. Start with a **Private** repository while you review the code and documentation. Do not initialize another README if uploading this one.
6. Create the repository, then use **uploading an existing file** or **Add file > Upload files**.
7. Unzip the deliverable. Upload the contents INSIDE `cyber-attack-classification`, including its subfolders. Do not upload only the ZIP, a virtual environment, or real datasets. Browser uploads may omit hidden files; use GitHub Desktop or Git to include `.gitignore`.
8. Commit the files with a message such as `Add tested post-publication research companion`.
9. Verify README rendering and the synthetic-demo chart. Run the quickstart yourself.
10. Review attribution, choose a software license if you want others to reuse the code, and decide when to make it public.

Optional Git upload, after creating an empty repository (replace YOUR-USERNAME):

```bash
git init
git add .
git commit -m "Add post-publication research companion"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/cyber-attack-classification.git
git push -u origin main
```

Authenticate using GitHub's supported sign-in flow. Never paste tokens or passwords into a README or notebook. Git identity configuration, if needed, should use your own chosen commit identity.

Once published, add the actual repository URL to `CITATION.cff` and link the repository from your portfolio. Do not assign the journal article's DOI to the software itself.

Official instructions: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
