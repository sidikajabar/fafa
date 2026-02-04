"""
Portal Command Handlers for Telegram Bot
Implements the /portal setup wizard and other portal commands
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

logger = logging.getLogger(__name__)

# Conversation states
(
    PORTAL_PUBLIC_CHANNEL,
    PORTAL_PRIVATE_GROUP,
    PORTAL_WELCOME_MESSAGE,
) = range(3)


async def portal_setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the portal setup wizard"""
    await update.message.reply_text(
        "🔐 *Portal Setup Wizard*\n\n"
        "*Step 1/3: Public Channel*\n\n"
        "Please forward a message from your public channel or send the channel username "
        "(e.g., @yourchannel).\n\n"
        "⚠️ Make sure the bot is an admin in the channel!\n\n"
        "Send /cancel to cancel setup.",
        parse_mode='Markdown'
    )
    return PORTAL_PUBLIC_CHANNEL


async def portal_public_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Step 1: Public channel input"""
    message = update.message
    
    # Check if message is forwarded from a channel
    if message.forward_from_chat and message.forward_from_chat.type == 'channel':
        channel = message.forward_from_chat
        channel_id = channel.id
        channel_username = channel.username
        channel_title = channel.title
        
        # Verify bot is admin
        try:
            bot_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply_text(
                    "❌ I'm not an admin in that channel!\n\n"
                    "Please make me an admin and try again.",
                    parse_mode='Markdown'
                )
                return PORTAL_PUBLIC_CHANNEL
        except Exception as e:
            logger.error(f"Error checking bot admin status: {e}")
            await message.reply_text(
                "❌ Could not verify admin status. Make sure I'm an admin in the channel.\n\n"
                f"Error: {str(e)}",
                parse_mode='Markdown'
            )
            return PORTAL_PUBLIC_CHANNEL
        
        # Store channel info
        context.user_data['portal_setup'] = {
            'public_channel_id': channel_id,
            'public_channel_username': channel_username,
            'public_channel_title': channel_title
        }
        
        await message.reply_text(
            f"✅ Channel verified: *{channel_title}*\n\n"
            f"*Step 2/3: Private Group*\n\n"
            "Now, forward a message from your private group or send the group username/ID.\n\n"
            "⚠️ Make sure the bot is an admin in the group!",
            parse_mode='Markdown'
        )
        return PORTAL_PRIVATE_GROUP
    
    # Check if username was provided
    elif message.text and message.text.startswith('@'):
        channel_username = message.text[1:]  # Remove @
        
        try:
            # Try to get channel info
            channel = await context.bot.get_chat(f"@{channel_username}")
            
            if channel.type != 'channel':
                await message.reply_text(
                    "❌ That's not a channel!\n\n"
                    "Please send a channel username or forward a message from the channel.",
                    parse_mode='Markdown'
                )
                return PORTAL_PUBLIC_CHANNEL
            
            # Verify bot is admin
            bot_member = await context.bot.get_chat_member(channel.id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply_text(
                    "❌ I'm not an admin in that channel!\n\n"
                    "Please make me an admin and try again.",
                    parse_mode='Markdown'
                )
                return PORTAL_PUBLIC_CHANNEL
            
            # Store channel info
            context.user_data['portal_setup'] = {
                'public_channel_id': channel.id,
                'public_channel_username': channel_username,
                'public_channel_title': channel.title
            }
            
            await message.reply_text(
                f"✅ Channel verified: *{channel.title}*\n\n"
                f"*Step 2/3: Private Group*\n\n"
                "Now, forward a message from your private group or send the group username/ID.\n\n"
                "⚠️ Make sure the bot is an admin in the group!",
                parse_mode='Markdown'
            )
            return PORTAL_PRIVATE_GROUP
            
        except Exception as e:
            logger.error(f"Error getting channel: {e}")
            await message.reply_text(
                "❌ Could not find that channel or I don't have access to it.\n\n"
                f"Error: {str(e)}\n\n"
                "Please:\n"
                "1. Make sure the username is correct\n"
                "2. Make me an admin in the channel\n"
                "3. Try forwarding a message from the channel instead",
                parse_mode='Markdown'
            )
            return PORTAL_PUBLIC_CHANNEL
    
    else:
        await message.reply_text(
            "❌ Invalid input!\n\n"
            "Please either:\n"
            "• Forward a message from your channel\n"
            "• Send the channel username (e.g., @yourchannel)",
            parse_mode='Markdown'
        )
        return PORTAL_PUBLIC_CHANNEL


async def portal_private_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Step 2: Private group input"""
    message = update.message
    
    # Check if message is forwarded from a group
    if message.forward_from_chat and message.forward_from_chat.type in ['group', 'supergroup']:
        group = message.forward_from_chat
        group_id = group.id
        group_title = group.title
        
        # Verify bot is admin
        try:
            bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply_text(
                    "❌ I'm not an admin in that group!\n\n"
                    "Please make me an admin with 'Invite users' permission and try again.",
                    parse_mode='Markdown'
                )
                return PORTAL_PRIVATE_GROUP
            
            # Check if bot can create invite links
            if not bot_member.can_invite_users:
                await message.reply_text(
                    "❌ I don't have permission to create invite links!\n\n"
                    "Please give me 'Invite users via link' permission and try again.",
                    parse_mode='Markdown'
                )
                return PORTAL_PRIVATE_GROUP
                
        except Exception as e:
            logger.error(f"Error checking bot admin status: {e}")
            await message.reply_text(
                "❌ Could not verify admin status.\n\n"
                f"Error: {str(e)}",
                parse_mode='Markdown'
            )
            return PORTAL_PRIVATE_GROUP
        
        # Store group info
        context.user_data['portal_setup']['private_group_id'] = group_id
        context.user_data['portal_setup']['private_group_title'] = group_title
        
        await message.reply_text(
            f"✅ Group verified: *{group_title}*\n\n"
            f"*Step 3/3: Welcome Message*\n\n"
            "Send a custom welcome message for users (or /skip to use default).\n\n"
            "This message will be shown when users click the verify button.",
            parse_mode='Markdown'
        )
        return PORTAL_WELCOME_MESSAGE
    
    # Check if username/ID was provided
    elif message.text:
        group_identifier = message.text
        
        # Remove @ if present
        if group_identifier.startswith('@'):
            group_identifier = group_identifier[1:]
        
        try:
            # Try to get group info
            # Could be username or numeric ID
            if group_identifier.startswith('-'):
                # It's a chat ID
                group = await context.bot.get_chat(int(group_identifier))
            else:
                # It's a username
                group = await context.bot.get_chat(f"@{group_identifier}")
            
            if group.type not in ['group', 'supergroup']:
                await message.reply_text(
                    "❌ That's not a group!\n\n"
                    "Please send a group username/ID or forward a message from the group.",
                    parse_mode='Markdown'
                )
                return PORTAL_PRIVATE_GROUP
            
            # Verify bot is admin
            bot_member = await context.bot.get_chat_member(group.id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply_text(
                    "❌ I'm not an admin in that group!\n\n"
                    "Please make me an admin with 'Invite users' permission and try again.",
                    parse_mode='Markdown'
                )
                return PORTAL_PRIVATE_GROUP
            
            # Check if bot can create invite links
            if not bot_member.can_invite_users:
                await message.reply_text(
                    "❌ I don't have permission to create invite links!\n\n"
                    "Please give me 'Invite users via link' permission and try again.",
                    parse_mode='Markdown'
                )
                return PORTAL_PRIVATE_GROUP
            
            # Store group info
            context.user_data['portal_setup']['private_group_id'] = group.id
            context.user_data['portal_setup']['private_group_title'] = group.title
            
            await message.reply_text(
                f"✅ Group verified: *{group.title}*\n\n"
                f"*Step 3/3: Welcome Message*\n\n"
                "Send a custom welcome message for users (or /skip to use default).\n\n"
                "This message will be shown when users click the verify button.",
                parse_mode='Markdown'
            )
            return PORTAL_WELCOME_MESSAGE
            
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            await message.reply_text(
                "❌ Could not find that group or I don't have access to it.\n\n"
                f"Error: {str(e)}\n\n"
                "Please:\n"
                "1. Make sure the username/ID is correct\n"
                "2. Make me an admin in the group\n"
                "3. Try forwarding a message from the group instead",
                parse_mode='Markdown'
            )
            return PORTAL_PRIVATE_GROUP
    
    else:
        await message.reply_text(
            "❌ Invalid input!\n\n"
            "Please either:\n"
            "• Forward a message from your group\n"
            "• Send the group username (e.g., @yourgroup)\n"
            "• Send the group ID (e.g., -1001234567890)",
            parse_mode='Markdown'
        )
        return PORTAL_PRIVATE_GROUP


async def portal_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Step 3: Welcome message"""
    message = update.message
    
    # Get portal setup data
    setup_data = context.user_data.get('portal_setup', {})
    
    if not setup_data:
        await message.reply_text(
            "❌ Setup data lost. Please start over with /portal setup",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Handle skip or custom message
    if message.text and message.text == '/skip':
        welcome_message = None  # Will use default
    else:
        welcome_message = message.text
    
    # Create the portal
    from portal_service import PortalService
    portal_service = context.bot_data.get('portal_service')
    
    if not portal_service:
        await message.reply_text(
            "❌ Portal service not available. Please contact the bot admin.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    portal_id = await portal_service.create_portal(
        owner_id=update.effective_user.id,
        public_channel_id=setup_data['public_channel_id'],
        public_channel_username=setup_data['public_channel_username'],
        private_group_id=setup_data['private_group_id'],
        private_group_title=setup_data['private_group_title'],
        welcome_message=welcome_message
    )
    
    if portal_id:
        from portal_service import format_portal_setup_message
        success_message = format_portal_setup_message(
            portal_id,
            setup_data['public_channel_username'],
            setup_data['private_group_title']
        )
        await message.reply_text(success_message, parse_mode='Markdown')
    else:
        await message.reply_text(
            "❌ Failed to create portal. Please try again or contact support.",
            parse_mode='Markdown'
        )
    
    # Clear setup data
    context.user_data.pop('portal_setup', None)
    return ConversationHandler.END


async def portal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the portal setup"""
    context.user_data.pop('portal_setup', None)
    await update.message.reply_text(
        "❌ Portal setup cancelled.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END


# Create the conversation handler
def create_portal_conversation_handler():
    """Create and return the portal setup conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler('portal', portal_setup_start, filters.Regex('^setup$'))],
        states={
            PORTAL_PUBLIC_CHANNEL: [
                MessageHandler(
                    filters.TEXT | filters.FORWARDED,
                    portal_public_channel
                )
            ],
            PORTAL_PRIVATE_GROUP: [
                MessageHandler(
                    filters.TEXT | filters.FORWARDED,
                    portal_private_group
                )
            ],
            PORTAL_WELCOME_MESSAGE: [
                MessageHandler(
                    filters.TEXT,
                    portal_welcome_message
                ),
                CommandHandler('skip', portal_welcome_message)
            ],
        },
        fallbacks=[CommandHandler('cancel', portal_cancel)],
        name='portal_setup',
        persistent=False
    )
