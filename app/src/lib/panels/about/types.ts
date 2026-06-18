import type { Component } from "svelte";

export interface TechItem {
  name: string;
  description: string;
  color: string;
  link: string;
  features: string[];
  logo: string;
}

export interface FeatureItem {
  title: string;
  description: string;
  icon: Component;
  gradient: string;
}
