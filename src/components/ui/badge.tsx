import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'secondary' | 'destructive' | 'outline';
}

export const Badge: React.FC<BadgeProps> = ({ children, className, variant = 'default' }) => (
  <span className={className}>{children}</span>
);
