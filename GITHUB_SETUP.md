# GitHub Repository Setup Instructions

Follow these steps to create a new GitHub repository and push KoraFlow to it.

## Step 1: Create Repository on GitHub

1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the repository details:
   - **Repository name**: `KoraFlow` (or your preferred name)
   - **Description**: "A white-label, modular, enterprise platform powered by Frappe Framework with a local LLaMA-based RAG system"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

## Step 2: Push to GitHub

After creating the repository, GitHub will show you the repository URL. Use one of these methods:

### Option A: Use the Push Script (Recommended)

```bash
./push_to_github.sh
```

The script will prompt you for your repository URL and then push everything.

### Option B: Manual Push

If you prefer to do it manually:

```bash
# Add the remote (replace with your actual repository URL)
git remote add origin https://github.com/YOUR_USERNAME/KoraFlow.git

# Or if you prefer SSH:
git remote add origin git@github.com:YOUR_USERNAME/KoraFlow.git

# Push to GitHub
git push -u origin main
```

## Step 3: Verify

After pushing, visit your repository on GitHub to verify all files are there.

## Repository URL Format

- HTTPS: `https://github.com/YOUR_USERNAME/KoraFlow.git`
- SSH: `git@github.com:YOUR_USERNAME/KoraFlow.git`

Replace `YOUR_USERNAME` with your actual GitHub username.

## Troubleshooting

### Authentication Issues

If you get authentication errors:

1. **For HTTPS**: You may need to use a Personal Access Token instead of a password
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate a new token with `repo` permissions
   - Use the token as your password when prompted

2. **For SSH**: Make sure your SSH key is added to GitHub
   - Check: `ssh -T git@github.com`
   - If not set up, follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Large File Warnings

If you see warnings about large files in the `bench/` directory, that's normal. The bench directory contains cloned repositories that are tracked as git submodules.

