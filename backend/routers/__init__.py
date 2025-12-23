# Import all routers
from .auth import router as auth_router
from .posts import router as posts_router
from .votes import router as votes_router
from .comments import router as comments_router
from .comment_actions import router as comment_actions_router
from .notifications import router as notifications_router
from .comments_feed import router as comments_feed_router
from .comment_votes import router as comment_votes_router
