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

export function Tabs({ children, className, value, onValueChange }: TabsProps) {
  return <div className={className} data-value={value}>{children}</div>;
}

export function TabsList({ children, className }: TabsListProps) {
  return <div className={className}>{children}</div>;
}

export function TabsTrigger({ children, className, value }: TabsTriggerProps) {
  return <button className={className} data-value={value}>{children}</button>;
}

export function TabsContent({ children, className, value }: TabsContentProps) {
  return <div className={className} data-value={value}>{children}</div>;
}
