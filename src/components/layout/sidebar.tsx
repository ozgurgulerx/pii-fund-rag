"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquarePlus,
  Search,
  ChevronLeft,
  ChevronRight,
  MessageCircle,
  Star,
  Building2,
  Users,
  Bookmark,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { SAMPLE_CONVERSATIONS, SAMPLE_WATCHLIST } from "@/data/seed";
import type { Conversation, WatchlistItem } from "@/types";

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  onSelectConversation: (id: string) => void;
  activeConversationId?: string;
  onNewChat: () => void;
}

export function Sidebar({
  isCollapsed,
  onToggle,
  onSelectConversation,
  activeConversationId,
  onNewChat,
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredConversations = SAMPLE_CONVERSATIONS.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const savedConversations = filteredConversations.filter((c) => c.isSaved);
  const recentConversations = filteredConversations.filter((c) => !c.isSaved);

  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 56 : 280 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="h-full border-r border-border bg-surface-1 flex flex-col relative"
    >
      {/* Toggle button */}
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onToggle}
        className="absolute -right-3 top-14 z-10 h-6 w-6 rounded-full border border-border bg-surface-2 shadow-subtle"
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {isCollapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </Button>

      {/* New Chat Button */}
      <div className="p-3">
        <Button
          onClick={onNewChat}
          variant="gold"
          className={cn(
            "w-full justify-start gap-2",
            isCollapsed && "justify-center px-0"
          )}
        >
          <MessageSquarePlus className="h-4 w-4" />
          {!isCollapsed && <span>New Chat</span>}
        </Button>
      </div>

      {/* Search */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="px-3 pb-3"
          >
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-sm"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <ScrollArea className="flex-1">
        <div className="p-3 pt-0 space-y-4">
          {/* Saved Queries */}
          {!isCollapsed && savedConversations.length > 0 && (
            <Section
              title="Saved"
              icon={<Bookmark className="h-3.5 w-3.5" />}
            >
              {savedConversations.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conversation={conv}
                  isActive={conv.id === activeConversationId}
                  onClick={() => onSelectConversation(conv.id)}
                  isCollapsed={isCollapsed}
                />
              ))}
            </Section>
          )}

          {/* Recent */}
          {!isCollapsed && recentConversations.length > 0 && (
            <Section
              title="Recent"
              icon={<MessageCircle className="h-3.5 w-3.5" />}
            >
              {recentConversations.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conversation={conv}
                  isActive={conv.id === activeConversationId}
                  onClick={() => onSelectConversation(conv.id)}
                  isCollapsed={isCollapsed}
                />
              ))}
            </Section>
          )}

          {/* Collapsed state icons */}
          {isCollapsed && (
            <div className="flex flex-col items-center gap-2 pt-2">
              {SAMPLE_CONVERSATIONS.slice(0, 4).map((conv) => (
                <Button
                  key={conv.id}
                  variant={conv.id === activeConversationId ? "secondary" : "ghost"}
                  size="icon-sm"
                  onClick={() => onSelectConversation(conv.id)}
                  className="w-8 h-8"
                >
                  {conv.isSaved ? (
                    <Star className="h-4 w-4" />
                  ) : (
                    <MessageCircle className="h-4 w-4" />
                  )}
                </Button>
              ))}
            </div>
          )}

          <Separator className="my-4" />

          {/* Watchlist */}
          {!isCollapsed && (
            <Section
              title="Watchlist"
              icon={<Star className="h-3.5 w-3.5 text-gold" />}
            >
              {SAMPLE_WATCHLIST.map((item) => (
                <WatchlistItemComponent key={item.id} item={item} />
              ))}
            </Section>
          )}
        </div>
      </ScrollArea>
    </motion.aside>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
        {icon}
        <span>{title}</span>
      </div>
      {children}
    </div>
  );
}

function ConversationItem({
  conversation,
  isActive,
  onClick,
  isCollapsed,
}: {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
  isCollapsed: boolean;
}) {
  if (isCollapsed) return null;

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left px-2 py-1.5 rounded-lg text-sm transition-colors",
        "hover:bg-surface-2",
        isActive && "bg-surface-2 text-foreground",
        !isActive && "text-muted-foreground"
      )}
    >
      <div className="flex items-center gap-2">
        {conversation.isSaved && (
          <Star className="h-3 w-3 text-gold shrink-0" />
        )}
        <span className="truncate">{conversation.title}</span>
      </div>
    </button>
  );
}

function WatchlistItemComponent({ item }: { item: WatchlistItem }) {
  return (
    <button className="w-full text-left px-2 py-1.5 rounded-lg text-sm text-muted-foreground hover:bg-surface-2 hover:text-foreground transition-colors">
      <div className="flex items-center gap-2">
        {item.type === "company" ? (
          <Building2 className="h-3 w-3 shrink-0" />
        ) : (
          <Users className="h-3 w-3 shrink-0" />
        )}
        <span className="truncate">{item.name}</span>
      </div>
    </button>
  );
}
