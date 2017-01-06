library(dplyr)
library(readr)
library(tidyr)
library(ggplot2)
library(magrittr)

#----------
# Data Load
#----------

# full term data
term_data <-
  read_csv('./output/dtm_source_counts.csv')

top_terms_left <-
  read_csv('./output/ngrams_top10000_left.csv')

top_terms_right <-
  read_csv('./output/ngrams_top10000_right.csv')

# alignment data
alignment_data <-
  read_csv('./output/source_info.csv') %>%
  rename(site_side = side)

#---------------
# Data Transform
#---------------

# transform full term data to long
term_data_long <-
  term_data %>%
  gather(key = base_url, value = term_count, -term) %>%
  left_join(alignment_data, by = 'base_url')

# total terms for normalization
left_terms <- sum(term_data_long$term_count[term_data_long$site_side == 'left'])
right_terms <- sum(term_data_long$term_count[term_data_long$site_side == 'right'])

# calculate term distribution between left and right sources
term_data_long %<>%
  group_by(term) %>%
  mutate(# calculate how the terms are distributed between left and right sources
         left_share = sum(term_count[site_side == 'left']) / left_terms,
         right_share = sum(term_count[site_side == 'right']) / right_terms,
         term_align = left_share / (right_share + left_share)) %>%
  ungroup

# transform top term data to long
full_data <-
  bind_rows(
    top_terms_left,
    top_terms_right
  ) %>%
  inner_join(term_data_long, by = 'term')

#---------------
# Prep Plot Data
#---------------

# term alignment plot data
pdat_align <-
  term_data_long %>%
  group_by(term, term_align) %>%
  summarize(term_count = sum(term_count)) %>%
  ungroup %>%
  filter(term_count > quantile(term_count, .05))

# term tf-idf group by rank, side, and term for plotting
pdat_term <-
  full_data %>%
  group_by(rank, side, term, tfidf, left_share, right_share, term_align) %>%
  arrange(desc(term_count)) %>%
  
  summarise(# summarize the sites most associated with each term
            `Top Sites` = paste0(base_url[1:3], ' (', term_count[1:3], ')',
                               collapse = ', '),
            
            # count total times term appears
            `Total Count` = sum(term_count)) %>%
  ungroup %>%
  mutate(side = recode(side, left = 'Left', right = 'Right')) %>%
  rename(`Tf-idf` = tfidf)

# summary stats alignment
align_mean <- mean(pdat_align$term_align)
align_sd <- sd(pdat_align$term_align)

#-------------
# Create Plots
#-------------
pdat_align %>%
  
  # plot
  ggplot(aes(x = 1 - term_align)) +
  geom_vline(xintercept = c(align_mean - align_sd,
                            align_mean,
                            align_mean + align_sd),
             alpha = 0.9, color = '#4F5559', size = 1.05) +
  
  geom_histogram(aes(y= ..density..), bins = 80, fill = '#beaed4', alpha = 0.8) +
  
  # labels
  labs(x = 'Share of Term Appearance in Right-Aligned Sources',
       y = 'Density',
       title = 'Distribution of Term Alignment',
       subtitle = '(for top 95% of terms by count, mean and std. dev. shown)') +
  scale_x_continuous(label = scales::percent) +
  
  # theming
  scale_fill_gradient2(#midpoint = align_mean,
                       mid = '#4F5559', guide=FALSE) +
  theme_bw() +
  theme(text = element_text(family = 'Calibri'))

ggsave('./output/term_alignment_dist.png', width = 6, height = 4)

# Plot out the term data, arranged by ranked tf-idf
plot_term_data <- function(dat, alignment_level){
  
  # filter data to only display top 100 terms for each side
  dat %>%
    filter(abs(align_mean - term_align) >= alignment_level) %>%
    group_by(side) %>%
    arrange(side, desc(`Tf-idf`)) %>%
    mutate(plotrank = seq(n())) %>%
    ungroup %>%
    arrange(plotrank) %>%
    slice(seq(200)) %>%
    mutate(`Term Alignment` = 1 - term_align) %>%
    
    # plot
    ggplot(aes(x = side, y = plotrank, color = term_align)) +
    geom_text(aes(label = term, size = abs(term_align - align_mean))) +
    scale_y_reverse() +
    
    # labels
    geom_point(aes(t1 = `Tf-idf`,
                   t2 = `Total Count`,
                   t3 = `Top Sites`,
                   t4 = `Term Alignment`),
               alpha = 0) +
    labs(x = '', y = 'Ranked Tf-idf',
         title = 'n-grams Ranked by Tf-idf for Left- and Right-Aligned Sources',
         subtitle = '(size & color represent term partisanship)') +
    
    # themes
    scale_colour_gradient2(midpoint = align_mean,
                           mid = '#4F5559', guide=FALSE) +
    scale_size_continuous(guide=FALSE, range = c(2, 6)) +
    scale_x_discrete(position = 'top') + 
    theme(line = element_blank(),
          rect = element_blank(),
          
          axis.text.y = element_blank(),
          axis.text.x = element_text(size = 12, face = 'bold'))
}


plot_term_data(pdat_term, 0) %>%
  plotly::ggplotly(tooltip=c('t1', 't2', 't3', 't4'), height = 2000) %>%
  htmlwidgets::saveWidget(file='term_align_nofilter.html')

plot_term_data(pdat_term, align_sd) %>%
  plotly::ggplotly(tooltip=c('t1', 't2', 't3', 't4'), height = 2000) %>%
  htmlwidgets::saveWidget(file='term_align_1sdfilter.html')