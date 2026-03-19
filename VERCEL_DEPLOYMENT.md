# Vercel Deployment Guide

This document provides information about deploying this application to Vercel.

## Configuration

The application uses a `vercel.json` file to configure the Vercel deployment. The configuration includes:

- Build settings using `@vercel/static-build`
- Custom build command that handles symlinks and runs the build process
- Routes configuration for serving static assets and the SPA
- Environment variables for production deployment

## Environment Variables

The following environment variables should be set in the Vercel dashboard:

### Required Environment Variables

- `NODE_ENV`: Set to `production` for production deployments
- `CI`: Set to `false` to prevent treating warnings as errors during build
- `REACT_APP_USE_MOCK_DATA`: Set to `false` for production deployments to use real data

### Firebase Configuration (if using Firebase)

If your application uses Firebase, you'll need to set the following environment variables in the Vercel dashboard:

- `REACT_APP_FIREBASE_API_KEY`: Your Firebase API key
- `REACT_APP_FIREBASE_AUTH_DOMAIN`: Your Firebase auth domain
- `REACT_APP_FIREBASE_PROJECT_ID`: Your Firebase project ID
- `REACT_APP_FIREBASE_STORAGE_BUCKET`: Your Firebase storage bucket
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`: Your Firebase messaging sender ID
- `REACT_APP_FIREBASE_APP_ID`: Your Firebase app ID

## Deployment Process

1. Push your code to a Git repository
2. Connect the repository to Vercel
3. Configure the environment variables in the Vercel dashboard
4. Deploy the application

## Troubleshooting

If you encounter issues during deployment, check the following:

- Ensure all required environment variables are set correctly
- Check the build logs for any errors
- Verify that the `vercel.json` configuration is correct for your application