# Releasing llm-kasten

## First-time setup

1. Create the GitHub repo at github.com/jordan-gibbs/kasten
2. Push the code:
   ```bash
   git init
   git add -A
   git commit -m "Initial release v0.1.0"
   git branch -M main
   git remote add origin git@github.com:jordan-gibbs/kasten.git
   git push -u origin main
   ```
3. Enable branch protection on `main`:
   - Settings > Branches > Add rule for `main`
   - Require pull request reviews
   - Require status checks to pass (select the CI workflow)
4. Set up PyPI trusted publisher:
   - Go to pypi.org > Your projects > Publishing
   - Add a new pending publisher:
     - Owner: jordan-gibbs
     - Repository: kasten
     - Workflow: publish.yml
     - Environment: (leave blank)
5. Create the first release:
   - GitHub > Releases > Create new release
   - Tag: `v0.1.0`
   - Title: `v0.1.0`
   - Auto-generate release notes
   - Publish -- this triggers the PyPI publish workflow

## Subsequent releases

1. Update version in `pyproject.toml` and `src/kasten/__init__.py`
2. Update `CHANGELOG.md` with new entries
3. Commit, push, merge to main
4. Create a GitHub release with the new tag
5. The publish workflow handles PyPI automatically
