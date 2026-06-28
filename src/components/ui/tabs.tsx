import React from "react";

export interface TabsProps {
  children: React.ReactNode;
  className?: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

export interface TabsListProps {
  children: React.ReactNode;
  className?: string;
}

export interface TabsTriggerProps {
  children: React.ReactNode;
  value?: string;
  className?: string;
}

export interface TabsContentProps {
  children: React.ReactNode;
  value?: string;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ children, className, value, onValueChange }) => {
  return <div className={className} data-value={value}>{children}</div>;
};

export const TabsList: React.FC<TabsListProps> = ({ children, className }) => {
  return <div className={className}>{children}</div>;
};

export const TabsTrigger: React.FC<TabsTriggerProps> = ({ children, className, value }) => {
  return <button className={className} data-value={value}>{children}</button>;
};

export const TabsContent: React.FC<TabsContentProps> = ({ children, className, value }) => {
  return <div className={className} data-value={value}>{children}</div>;
};
