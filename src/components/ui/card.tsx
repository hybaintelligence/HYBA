import React from "react";

export interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className }) => (
  <div className={className}>{children}</div>
);

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => (
  <div className={className}>{children}</div>
);

export const CardTitle: React.FC<CardTitleProps> = ({ children, className }) => (
  <h3 className={className}>{children}</h3>
);

export const CardDescription: React.FC<CardDescriptionProps> = ({ children, className }) => (
  <p className={className}>{children}</p>
);

export const CardContent: React.FC<CardContentProps> = ({ children, className }) => (
  <div className={className}>{children}</div>
);
