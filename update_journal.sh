#!/bin/bash
# Remove the English journal entry and append the Korean version
sed -i '/## 2024-08-17 - Swagger UI Auth Persistence/,/EOF/d' .jules/palette.md
sed -i '/Added "persistAuthorization"/d' .jules/palette.md
